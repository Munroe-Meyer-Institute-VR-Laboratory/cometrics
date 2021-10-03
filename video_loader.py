'''
https://github.com/WelkinU/ThreadedVideoLoader/blob/master/VideoLoader.py
Implements a multi-threaded wrapper to OpenCV's VideoCapture, that behaves like a
List and/or Generator Object. Should be compatible with all applicable OpenCV versions.
Supports video files and video streams (webcam, http stream, etc.)
'''

import cv2
import threading
import queue
import inspect


class VideoLoader():
    ''' Implements a wrapper to OpenCV's VideoCapture, that behaves like a Python Object.
    Should be compatible with all applicable OpenCV versions. Support for threading to speed up
    video read operations.
    Based on code here: https://github.com/WelkinU/ThreadedVideoLoader
    '''

    def __init__(self, video_path, use_threading = True, precache_frames = False, return_slices_as_iterator = False,
                    max_queue_size = 20, image_transform = None, width = None, height = None):
        ''' Initialize Video Loader
        video_path {str} -- Filepath to the video (path/to/video.mp4). Alternatively, use 0 for webcam (or 1 for your second webcam).
        use_threading {bool} -- If True, uses background thread to pre-caches frames in memory for speed.
                                If False, uses standard VideoCapture to grab frames on the fly. (Default {True})
        precache_frames {bool} -- Load all video frames into memory during object initialization to increase speed of other operations.
                                  The speedup is particularly noticable when doing large list-like slicing on the videos. (Default {False})
        max_queue_size {int} -- Maximum number of frames to cache in memory. Used only when use_threading = True. (Default {20})
        image_transform {function} -- A convenience feature for applying an image transform function to all image output.
                                      Must be a function that accepts only an image for input.
                                      Leaving this as None means no transform is applied to output. (Default {None})
        width {int} -- Override the default OpenCV capture dimensions - sometimes OpenCV gets incorrect webcam dimensions. (Default {None})
        height {int} -- Override the default OpenCV capture dimensions - sometimes OpenCV gets incorrect webcam dimensions. (Default {None})
        '''
        self.cap = cv2.VideoCapture(video_path)
        self.video_path = video_path
        self.image_transform = image_transform
        self.return_slices_as_iterator = return_slices_as_iterator

        '''video properties - for more see: https://docs.opencv.org/2.4/modules/highgui/doc/reading_and_writing_images_and_video.html
            Note the constants names changed between OpenCV versions. Versions >= 3 don't have the "CV_" at the beginning.
        '''
        if cv2.__version__[0] >= '3':
            #for OpenCV versions >= 3, they have the constant names without the "CV_" at the beginning
            self.fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.video_codec = int(self.cap.get(cv2.CAP_PROP_FOURCC))

            if height is None:
                self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            else:
                self.height = height
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

            if width is None:
                self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            else:
                self.width = width
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)

            self.pos_frames_number = cv2.CAP_PROP_POS_FRAMES
        else:
            #for OpenCV versions < 2, they have the constant names with an the "CV_" at the beginning
            self.fps = self.cap.get(cv2.CV_CAP_PROP_FPS)
            self.frame_count = int(self.cap.get(cv2.CV_CAP_PROP_FRAME_COUNT))
            self.video_codec = int(self.cap.get(cv2.CV_CAP_PROP_FOURCC))

            if height is None:
                self.height = int(self.cap.get(cv2.CV_CAP_PROP_FRAME_HEIGHT))
            else:
                self.height = height
                self.cap.set(cv2.CV_CAP_PROP_FRAME_HEIGHT, height)

            if width is None:
                self.width = int(self.cap.get(cv2.CV_CAP_PROP_FRAME_WIDTH))
            else:
                self.width = width
                self.cap.set(cv2.CV_CAP_PROP_FRAME_WIDTH, width)

            self.pos_frames_number = cv2.CV_CAP_PROP_POS_FRAMES

        #handle threading
        self.use_threading = use_threading
        self.thread = None
        if self.use_threading:
            self.thread_started = False
            self.frame_queue = queue.Queue(maxsize = max_queue_size)
            self.first_queue_full_warning_displayed = False

        self.precache_frames = False
        if precache_frames:
            print('Caching frames...')
            if self.frame_count < 0:
                print('WARNING: For video streams (webcam, http stream, etc) this operation is not supported.')

            self.frame_cache = list(self.__iter__())
            self.precache_frames = True #important that this be AFTER self.frame_cache is generated by __iter__()

    def __getitem__(self,idx):
        ''' Magic Function so you can use the [] operator to index into this object
        Used only when the frames are stored ie. webcam not supported for this function.
        Assumes index is within +/- video frame count. If outside of that range, it raises an error.
        '''
        assert self.frame_count >= 0, 'Operation not supported for video streams(webcam, http stream, etc)'
        if self.precache_frames:
            return self.frame_cache[idx]

        if isinstance(idx,slice):
            step = idx.step if idx.step else 1
            if self.return_slices_as_iterator and step > 0:
                return self.get_series_of_frames_iterator(start_frame = idx.start, end_frame = idx.stop, step = abs(step))
            else:
                frame_list = self.get_series_of_frames(start_frame = idx.start, end_frame = idx.stop, step = abs(step))
                return frame_list if idx.step>0 else frame_list[::-1]
        else:
            if self.frame_count > idx >= -self.frame_count and isinstance(idx,int):
                cur_frame_pos = self.get_frame_position() #save current frame position so this method doesn't interfere with __iter__() or __next__()

                self.cap.set(self.pos_frames_number, idx%self.frame_count)
                ret,frame=self.cap.read()

                self.cap.set(self.pos_frames_number, cur_frame_pos) #reset current frame position so this method doesn't interfere with __iter__() or __next__()

                return self.apply_transform(frame)
            else:
                raise IndexError(
                    f'''Frame Index is {idx}. Frame Index needs to be a int that is less than the number of frames in the video. 
                    If Frame Index is negative, it must have an absolute value less than or equal to the frame count''')

    def __iter__(self):
        '''Magic Function so you can call this as an iterator. Ex: for frame in VideoLoader('myvideo.mp4')'''
        if self.precache_frames:
            return self.frame_cache

        if self.use_threading:
            if not self.thread_started:
                self.start_thread()
            while self.thread_started:
                frame = self.frame_queue.get(block = True, timeout = 30) #timeout is in seconds
                if frame is None:
                    break
                else:
                    yield self.apply_transform(frame)
            self.stop_thread()
        else:
            ret = True
            while ret:
                ret,frame=self.cap.read()
                yield self.apply_transform(frame)
        self.cap.set(self.pos_frames_number, 0) #reset frame position to 0, in case __iter__() is called multiple times sequentially

    def __next__(self):
        '''Magic Function so you use the next() function on this object.'''
        if self.use_threading:
            if not self.thread_started:
                self.start_thread()
            frame = self.frame_queue.get(block = True, timeout = 30) #timeout is in seconds
            if frame is None:
                raise StopIteration
            else:
                yield self.apply_transform(frame)
        else:
            ret,frame=self.cap.read()
            if ret >= self.frame_count:
                self.cap.set(self.pos_frames_number, 0)
                raise StopIteration
            else:
                return self.apply_transform(frame)

    def __repr__(self):
        '''Magic Function so you can use the print() function on this object.
        Using inspect to fix the triple commented string issue per this. Textwrap module didn't work due to leading line issue.
        https://stackoverflow.com/questions/1412374/how-to-remove-extra-indentation-of-python-triple-quoted-multi-line-strings/47417848#47417848
        '''
        ret = f'''-------------VideoLoader Object-------------
                    Video Source: {self.video_path}
                    Threaded: {self.use_threading}
                    Image Transform: {"Yes" if self.image_transform else "No"}
                    Height: {self.height}
                    Width: {self.width}
                    Length: {self.frame_count}
                    FPS: {self.fps}
                    Video Codec: {self.video_codec}
                    Precached frames: {self.precache_frames}
                    Slicing Returns Iterator (Default=List): {self.return_slices_as_iterator}
                    --------------------------------------------
                    '''
        return inspect.cleandoc(ret)

    def __len__(self):
        '''Magic Function so you can use the len() function on this object.'''
        return self.frame_count

    def __enter__(self):
        return self

    def __exit__(self):
        #print('Releasing resources.')
        if self.use_threading:
            self.stop_thread()
        self.cap.release()

    def __del__(self):
        self.__exit__()

    def release(self):
        self.__exit__()

    def get_series_of_frames(self, start_frame = None, end_frame = None, step = 1):
        '''Helper function for __getitem__()
        Returns series of frames from the video from start_frame (inclusive) to end_frame (not inclusive).
        Step is to process every Nth frame, for example step = 3 returns every 3rd frame.'''
        assert self.frame_count >= 0, 'Operation not supported for video streams(webcam, http stream, etc)'

        if start_frame is None:
            start_frame = 0

        if end_frame is None:
            end_frame = self.frame_count-1

        if end_frame < 0:
            end_frame += self.frame_count #allow user to put in end frame with negative index

        if self.frame_count > end_frame >= start_frame >= 0:
            cur_frame_pos = self.get_frame_position() #save current frame position so this method doesn't interfere with __iter__() or __next__()
            frame_list = []
            self.cap.set(self.pos_frames_number, start_frame)
            #reading all the frames is faster than seeking according to this:
            #https://stackoverflow.com/questions/52655841/opencv-python-multithreading-seeking-within-a-videocapture-object
            for idx, frame in enumerate(self.__iter__()):
                if start_frame + idx >= end_frame:
                    break
                if idx % step == 0:
                    frame = self.apply_transform(frame)
                    frame_list.append(frame)

            self.stop_thread() #to prevent error "Assertion fctx->async_lock failed at libavcodec/pthread_frame.c:155"
            self.cap.set(self.pos_frames_number, cur_frame_pos) #reset current frame position so this method doesn't interfere with __iter__() or __next__()
            return frame_list
        else:
            raise IndexError(
                f'''Inputs must satisfy frame_count > end_frame >= start_frame >= 0. Start Frame = {start_frame}. End frames = {end_frame}. Frame count = {self.frame_count}.''')

    def get_series_of_frames_iterator(self, start_frame = None, end_frame = None, step = 1):
        '''Helper function for __getitem__()
        Returns series of frames from the video from start_frame (inclusive) to end_frame (not inclusive).
        Step is to process every Nth frame, for example step = 3 returns every 3rd frame.'''
        assert self.frame_count >= 0, 'Operation not supported for video streams(webcam, http stream, etc)'
        assert step > 0, 'Invalid step for iterator. OpenCV cant easily iterate through videos in reverse'

        if start_frame is None:
            start_frame = 0

        if end_frame is None:
            end_frame = self.frame_count-1

        if end_frame < 0:
            end_frame += self.frame_count #allow user to put in end frame with negative index

        if self.frame_count > end_frame >= start_frame >= 0:
            cur_frame_pos = self.get_frame_position() #save current frame position so this method doesn't interfere with __iter__() or __next__()

            self.cap.set(self.pos_frames_number, start_frame)
            #reading all the frames is faster than seeking according to
            #https://stackoverflow.com/questions/52655841/opencv-python-multithreading-seeking-within-a-videocapture-object
            for idx, frame in enumerate(self.__iter__()):
                if start_frame + idx >= end_frame:
                    break
                if idx % step == 0:
                    yield frame

            self.stop_thread() #to prevent error "Assertion fctx->async_lock failed at libavcodec/pthread_frame.c:155"
            self.cap.set(self.pos_frames_number, cur_frame_pos) #reset current frame position so this method doesn't interfere with __iter__() or __next__()
        else:
            raise IndexError(
                f'''Inputs must satisfy frame_count > end_frame >= start_frame >= 0. Start Frame = {start_frame}. End frames = {end_frame}. Frame count = {self.frame_count}.''')

    def set(self, var1, var2):
        self.cap.set(var1, var2)

    def get_frame_position(self):
        return self.cap.get(self.pos_frames_number)

    def apply_transform_to_video(self,output_video_path=None,output_video_codec = None, fps = None, start = 0, end = None, step = 1, enable_start_stop_with_keypress = False):
        ''' Apply image_transform to video.
        output_video_path {str} -- Filepath to the output video (ex. path/to/video.mp4). Defaults behavior is as follows:
                                    If input video is my/video/test.mp4, default output is my/video/test_transformed.mp4
        output_video_codec {cv2 VideoCodec Object or Str} -- If input is cv2 VideoCodec object, use that codec
                                                            If input is string, attempt to convert that to VideoCodec object (example string input: 'mp4v')
                                                            Default behavior is to use same video codec as input video file, or if input is a webcam, use mp4v
        fps {int/float} -- The video frames per second. Default is same FPS as video file or webcam. If FPS not detected properly, default is 24 FPS.
        start {int} -- Start frame number - useful for processing only a portion of the video.
        end {int} -- End frame number - useful for processing only a portion of the video. Defaults to end of video
        start {int} -- Step ie. process every Nth frame - useful for processing only a portion of the video.
        enable_start_stop_with_keypress {bool} -- This allows you to start/stop recording with a keypress. Feature is intended solely for ease of use in saving webcam frames.
                                                    Not recommended for usage with video files.
        '''


        if self.image_transform is None:
            print('WARNING: No image transform selected.')

        if output_video_path is None:
            output_video_path = self.video_path[:-4] + "_transformed" + self.video_path[-4:]

        if output_video_codec is None:
            output_video_codec = self.video_codec if self.frame_count > 0 else 'mp4v' #use same video codec if video file, for webcam defualt to mp4v

        if isinstance(output_video_codec,str):
            if output_video_codec == 'mp4': #just in case someone puts in mp4 intending mp4v
                output_video_codec = 'mp4v'

            output_video_codec = cv2.VideoWriter_fourcc(*output_video_codec)

        if fps is None:
            fps = self.fps

        if fps <= 0:
            print(f'WARNING: FPS {fps} < 0, using FPS = 24 instead')
            fps = 24

        if enable_start_stop_with_keypress:
            windowName = 'PRESS ANY KEY TO START RECORDING FRAMES'
            for frame in self.__iter__():
                cv2.imshow(windowName, frame)
                if 0 <= cv2.waitKey(30):
                    break
            cv2.destroyWindow(windowName)

        print(f'Creating transformed video: {output_video_path}')
        vid_writer = cv2.VideoWriter(output_video_path, output_video_codec, fps, (self.width,self.height))
        for frame in self.get_series_of_frames_iterator(start,end,step):
            vid_writer.write(frame)

            if enable_start_stop_with_keypress:
                cv2.imshow('PRESS ANY KEY TO STOP DUMPING FRAMES',frame)
                if 0 <= cv2.waitKey(1):
                    break

        vid_writer.release()
        print('Done.')
        return 0

    def dump_frames_from_video(self, output_folder, file_format = 'frame{:05d}.jpg', start = 0, end = None, step = 1, enable_start_stop_with_keypress = False):
        ''' Use this to dump frames from a video or webcam
        output_folder {str} -- Folder to dump the output files to.
        file_format {str} -- The file name and format to dump frames to. The first {} in the format is replaced with the frame number.
                             Ex. frame{:05d}.jpg dumps frames as frame00000.jpg, frame00001.jpg, etc.
        start {int} -- Start frame number - useful for processing only a portion of the video.
        end {int} -- End frame number - useful for processing only a portion of the video. Defaults to end of video
        start {int} -- Step ie. process every Nth frame - useful for processing only a portion of the video.
        enable_start_stop_with_keypress {bool} -- This allows you to start/stop recording with a keypress. Feature is intended solely for ease of use in saving webcam frames.
                                                    Not recommended for usage with video files.
        '''

        if enable_start_stop_with_keypress:
            windowName = 'PRESS ANY KEY TO START RECORDING FRAMES'
            for frame in self.__iter__():
                cv2.imshow(windowName, frame)
                if 0 <= cv2.waitKey(30):
                    break
            cv2.destroyWindow(windowName)

        if end is None:
            end = self.frame_count-1

        for idx,frame in zip(range(start,end,step),self.get_series_of_frames_iterator(start,end,step)):
            cv2.imwrite(output_folder + '/' + file_format.format(idx), frame) #can put this in a thread for speed when using webcam

            if enable_start_stop_with_keypress:
                cv2.imshow('PRESS ANY KEY TO STOP DUMPING FRAMES',frame)
                if 0 <= cv2.waitKey(1):
                    break

    def apply_transform(self,frame):
        return frame if self.image_transform is None else self.image_transform(frame)

    #----------------------------------THREADING SPECIFIC FUNCTIONS----------------------------------
    def start_thread(self):
        if self.thread_started:
            print('Thread already started!')
            return
        with self.frame_queue.mutex:
            self.frame_queue.queue.clear() #clear the queue - in case it already has stuff in it

        self.thread_started = True
        self.thread = threading.Thread(target = self.update_thread, daemon = True, args =())
        self.thread.start()

    def update_thread(self):
        ret = True

        while ret and self.thread_started:
            ret, frame = self.cap.read()

            try:
                self.frame_queue.put(frame,block=True, timeout = 1) #timeout is in seconds, on last read, None is put into the Queue conveniently
            except queue.Full:
                #Current behavior is that if the queue is full and the main process has not exited, then we start dropping frames
                if not self.thread_started:
                    break
                else:
                    if not self.first_queue_full_warning_displayed:
                        self.first_queue_full_warning_displayed=True
                        print('Warning background thread has filled up frame queue storage. Future frames may be dropped if input is a video stream.')

                        #continue attmpting the next frame into the queue until it's read by the main thread or the main thread has stopped
                        while self.thread_started:
                            try:
                                self.frame_queue.put(frame,block=True, timeout = 1)
                                break
                            except:
                                pass

        self.thread_started = False

    def stop_thread(self):
        self.thread_started = False
        self.thread.join()