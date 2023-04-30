import csv
import glob
import json
import os
import pathlib
import threading
import tkinter
import warnings
from datetime import datetime
from enum import IntEnum
from tkinter import messagebox

import neurokit2 as nk
from flirt.stats.common import get_stats
from flirt.eda.feature_calculation import __cvx_eda
import numpy as np
import pandas as pd
import traces
from pyempatica import EmpaticaE4

from tkinter_utils import center

warnings.filterwarnings('ignore')


class EmpaticaData(IntEnum):
    ACC_3D = 0
    ACC_X = 1
    ACC_Y = 2
    ACC_Z = 3
    ACC_TIMESTAMPS = 4
    BVP = 5
    BVP_TIMESTAMPS = 6
    EDA = 7
    EDA_TIMESTAMPS = 8
    TMP = 9
    TMP_TIMESTAMPS = 10
    TAG = 11
    TAG_TIMESTAMPS = 12
    IBI = 13
    IBI_TIMESTAMPS = 14
    BAT = 15
    BAT_TIMESTAMPS = 16
    HR = 17
    HR_TIMESTAMPS = 18


date_format = "%B %d, %Y"
time_format = "%H:%M:%S"
datetime_format = date_format + time_format
accx_header = ['ACCX_mean', 'ACCX_std', 'ACCX_min', 'ACCX_max', 'ACCX_ptp', 'ACCX_sum', 'ACCX_energy', 'ACCX_skewness',
               'ACCX_kurtosis', 'ACCX_peaks', 'ACCX_rms',
               'ACCX_lineintegral', 'ACCX_n_above_mean', 'ACCX_n_below_mean', 'ACCX_n_sign_changes', 'ACCX_iqr',
               'ACCX_iqr_5_95', 'ACCX_pct_5', 'ACCX_pct_95',
               'ACCX_entropy', 'ACCX_perm_entropy', 'ACCX_svd_entropy']
accy_header = ['ACCY_mean', 'ACCY_std', 'ACCY_min', 'ACCY_max', 'ACCY_ptp', 'ACCY_sum', 'ACCY_energy', 'ACCY_skewness',
               'ACCY_kurtosis', 'ACCY_peaks', 'ACCY_rms',
               'ACCY_lineintegral', 'ACCY_n_above_mean', 'ACCY_n_below_mean', 'ACCY_n_sign_changes', 'ACCY_iqr',
               'ACCY_iqr_5_95', 'ACCY_pct_5', 'ACCY_pct_95',
               'ACCY_entropy', 'ACCY_perm_entropy', 'ACCY_svd_entropy']
accz_header = ['ACCZ_mean', 'ACCZ_std', 'ACCZ_min', 'ACCZ_max', 'ACCZ_ptp', 'ACCZ_sum', 'ACCZ_energy', 'ACCZ_skewness',
               'ACCZ_kurtosis', 'ACCZ_peaks', 'ACCZ_rms',
               'ACCZ_lineintegral', 'ACCZ_n_above_mean', 'ACCZ_n_below_mean', 'ACCZ_n_sign_changes', 'ACCZ_iqr',
               'ACCZ_iqr_5_95', 'ACCZ_pct_5', 'ACCZ_pct_95',
               'ACCZ_entropy', 'ACCZ_perm_entropy', 'ACCZ_svd_entropy']
tmp_header = ['TMP_mean', 'TMP_std', 'TMP_min', 'TMP_max', 'TMP_ptp', 'TMP_sum', 'TMP_energy', 'TMP_skewness',
              'TMP_kurtosis', 'TMP_peaks', 'TMP_rms',
              'TMP_lineintegral', 'TMP_n_above_mean', 'TMP_n_below_mean', 'TMP_n_sign_changes', 'TMP_iqr',
              'TMP_iqr_5_95', 'TMP_pct_5', 'TMP_pct_95',
              'TMP_entropy', 'TMP_perm_entropy', 'TMP_svd_entropy']
eda_header = ['SCR_Peaks_N', 'SCR_Peaks_Amplitude_Mean',
              'SCR_mean', 'SCR_std', 'SCR_min', 'SCR_max', 'SCR_ptp', 'SCR_sum', 'SCR_energy', 'SCR_skewness',
              'SCR_kurtosis', 'SCR_peaks', 'SCR_rms',
              'SCR_lineintegral', 'SCR_n_above_mean', 'SCR_n_below_mean', 'SCR_n_sign_changes', 'SCR_iqr',
              'SCR_iqr_5_95', 'SCR_pct_5', 'SCR_pct_95',
              'SCR_entropy', 'SCR_perm_entropy', 'SCR_svd_entropy',
              'SCL_mean', 'SCL_std', 'SCL_min', 'SCL_max', 'SCL_ptp', 'SCL_sum', 'SCL_energy', 'SCL_skewness',
              'SCL_kurtosis', 'SCL_peaks', 'SCL_rms',
              'SCL_lineintegral', 'SCL_n_above_mean', 'SCL_n_below_mean', 'SCL_n_sign_changes', 'SCL_iqr',
              'SCL_iqr_5_95', 'SCL_pct_5', 'SCL_pct_95', 'SCL_entropy', 'SCL_perm_entropy', 'SCL_svd_entropy'
              ]
ppg_header = ['PPG_Rate_Mean', 'HRV_MeanNN', 'HRV_SDNN', 'HRV_SDANN1', 'HRV_SDNNI1',
              'HRV_SDANN2', 'HRV_SDNNI2', 'HRV_SDANN5', 'HRV_SDNNI5', 'HRV_RMSSD', 'HRV_SDSD', 'HRV_CVNN', 'HRV_CVSD',
              'HRV_MedianNN', 'HRV_MadNN', 'HRV_MCVNN', 'HRV_IQRNN', 'HRV_Prc20NN', 'HRV_Prc80NN', 'HRV_pNN50',
              'HRV_pNN20', 'HRV_MinNN', 'HRV_MaxNN', 'HRV_HTI', 'HRV_TINN', 'HRV_ULF', 'HRV_VLF', 'HRV_LF', 'HRV_HF',
              'HRV_VHF', 'HRV_LFHF', 'HRV_LFn', 'HRV_HFn', 'HRV_LnHF', 'HRV_SD1', 'HRV_SD2', 'HRV_SD1SD2', 'HRV_S',
              'HRV_CSI', 'HRV_CVI', 'HRV_CSI_Modified', 'HRV_PIP', 'HRV_IALS', 'HRV_PSS', 'HRV_PAS', 'HRV_GI', 'HRV_SI',
              'HRV_AI', 'HRV_PI', 'HRV_C1d', 'HRV_C1a', 'HRV_SD1d', 'HRV_SD1a', 'HRV_C2d', 'HRV_C2a', 'HRV_SD2d',
              'HRV_SD2a', 'HRV_Cd', 'HRV_Ca', 'HRV_SDNNd', 'HRV_SDNNa', 'HRV_DFA_alpha1', 'HRV_MFDFA_alpha1_Width',
              'HRV_MFDFA_alpha1_Peak', 'HRV_MFDFA_alpha1_Mean', 'HRV_MFDFA_alpha1_Max', 'HRV_MFDFA_alpha1_Delta',
              'HRV_MFDFA_alpha1_Asymmetry', 'HRV_MFDFA_alpha1_Fluctuation', 'HRV_MFDFA_alpha1_Increment', 'HRV_ApEn',
              'HRV_SampEn', 'HRV_ShanEn', 'HRV_FuzzyEn', 'HRV_MSEn', 'HRV_CMSEn', 'HRV_RCMSEn', 'HRV_CD', 'HRV_HFD',
              'HRV_KFD', 'HRV_LZC']


def find_indices(search_list, search_item):
    indices = []
    for (index, item) in enumerate(search_list):
        if item in search_item:
            indices.append(index)
    return indices


def convert_legacy_events_e4(legacy_events, session_start_time):
    for legacy_event in legacy_events:
        if type(legacy_event[1]) is list:
            event_times = legacy_event[1]
            legacy_event[3] = [session_start_time + event_times[0], session_start_time + event_times[1]]
        else:
            event_times = legacy_event[1]
            legacy_event[3] = session_start_time + event_times


def convert_legacy_e4_data(empatica_data):
    converted_data = [[] for _ in range(19)]
    for window in empatica_data:
        for i in range(0, 13):
            converted_data[i].extend(window[i])
    return converted_data


def convert_timezone(old_time_object):
    new_value_timestamp = old_time_object.timestamp()
    return datetime.utcfromtimestamp(new_value_timestamp)


def convert_timestamps(empatica_data):
    empatica_data[EmpaticaData.BAT_TIMESTAMPS] = [int(l) for l in empatica_data[EmpaticaData.BAT_TIMESTAMPS]]
    empatica_data[EmpaticaData.TAG_TIMESTAMPS] = [int(l) for l in empatica_data[EmpaticaData.TAG_TIMESTAMPS]]
    empatica_data[EmpaticaData.TMP_TIMESTAMPS] = [int(l) for l in empatica_data[EmpaticaData.TMP_TIMESTAMPS]]
    empatica_data[EmpaticaData.HR_TIMESTAMPS] = [int(l) for l in empatica_data[EmpaticaData.HR_TIMESTAMPS]]
    empatica_data[EmpaticaData.IBI_TIMESTAMPS] = [int(l) for l in empatica_data[EmpaticaData.IBI_TIMESTAMPS]]
    empatica_data[EmpaticaData.ACC_TIMESTAMPS] = [int(l) for l in empatica_data[EmpaticaData.ACC_TIMESTAMPS]]
    empatica_data[EmpaticaData.BVP_TIMESTAMPS] = [int(l) for l in empatica_data[EmpaticaData.BVP_TIMESTAMPS]]
    empatica_data[EmpaticaData.EDA_TIMESTAMPS] = [int(l) for l in empatica_data[EmpaticaData.EDA_TIMESTAMPS]]


def export_e4_metrics(root, prim_dir, reli_dir, output_dir, time_period=20):
    prim_files = glob.glob(f'{prim_dir}/**/*.json', recursive=True)
    reli_files = glob.glob(f'{reli_dir}/**/*.json', recursive=True)
    prim_filepaths = [_ for _ in prim_files if _.split("\\")[0]]
    reli_filepaths = [_ for _ in reli_files if _.split("\\")[0]]

    popup_root = tkinter.Toplevel(root)
    popup_root.config(bd=-2)
    popup_root.title("Processing")
    popup_root.geometry("250x100")
    popup_root.config(bg="white")
    center(popup_root)
    label_var = tkinter.StringVar(popup_root, value=f'Processing Session 0 / {len(prim_filepaths + reli_filepaths)}')
    text_label = tkinter.Label(popup_root, textvariable=label_var, font=('Purisa', 11), bg="white")
    text_label.place(x=125, y=50, anchor=tkinter.CENTER)

    prim_export = os.path.join(output_dir, "Primary")
    reli_export = os.path.join(output_dir, "Reliability")

    # Create directories if they don't exist
    if not os.path.exists(reli_export):
        os.mkdir(reli_export)
    if not os.path.exists(prim_export):
        os.mkdir(prim_export)

    e4_metrics_thread = threading.Thread(target=__e4_metrics_thread, args=(prim_filepaths, reli_filepaths, prim_export,
                                                                           reli_export, time_period, label_var,
                                                                           output_dir, popup_root))
    e4_metrics_thread.daemon = True
    e4_metrics_thread.start()


def __e4_metrics_thread(prim_filepaths, reli_filepaths, prim_export, reli_export, time_period, label_var, output_dir,
                        popup_root):
    e4_data_found = False
    file_count = 0
    if prim_filepaths and reli_filepaths:
        for file in prim_filepaths:
            file_count += 1
            label_var.set(f'Processing Session {file_count} / {len(prim_filepaths + reli_filepaths)}')
            e4_data_found |= process_e4_data(file, prim_export, time_period)
        for file in reli_filepaths:
            file_count += 1
            label_var.set(f'Processing Session {file_count} / {len(prim_filepaths + reli_filepaths)}')
            e4_data_found |= process_e4_data(file, reli_export, time_period)
        if e4_data_found:
            messagebox.showinfo("E4 Metrics Computed", "E4 sessions have been successfully analyzed!\n"
                                                       "Check in raw data folders for output CSV files.")
            os.startfile(output_dir)
        else:
            messagebox.showwarning("Warning", "No E4 data found in sessions!")
    else:
        messagebox.showwarning("Warning", "No sessions found!")
    popup_root.destroy()


def interpolate_e4_data(empatica_data):
    empatica_data[EmpaticaData.BVP], empatica_data[EmpaticaData.BVP_TIMESTAMPS] = \
        interpolate_data(empatica_data[EmpaticaData.BVP], empatica_data[EmpaticaData.BVP_TIMESTAMPS], 64.0)
    empatica_data[EmpaticaData.EDA], empatica_data[EmpaticaData.EDA_TIMESTAMPS] = \
        interpolate_data(empatica_data[EmpaticaData.EDA], empatica_data[EmpaticaData.EDA_TIMESTAMPS], 4.0)
    empatica_data[EmpaticaData.ACC_X], _ = \
        interpolate_data(empatica_data[EmpaticaData.ACC_X], empatica_data[EmpaticaData.ACC_TIMESTAMPS], 32.0)
    empatica_data[EmpaticaData.ACC_Y], _ = \
        interpolate_data(empatica_data[EmpaticaData.ACC_Y], empatica_data[EmpaticaData.ACC_TIMESTAMPS], 32.0)
    empatica_data[EmpaticaData.ACC_Z], empatica_data[EmpaticaData.ACC_TIMESTAMPS] = \
        interpolate_data(empatica_data[EmpaticaData.ACC_Z], empatica_data[EmpaticaData.ACC_TIMESTAMPS], 32.0)
    empatica_data[EmpaticaData.TMP], empatica_data[EmpaticaData.TMP_TIMESTAMPS] = \
        interpolate_data(empatica_data[EmpaticaData.TMP], empatica_data[EmpaticaData.TMP_TIMESTAMPS], 4.0)


def interpolate_data(empatica_data, timestamps, sampling_rate):
    data = []
    for i in range(0, len(empatica_data)):
        data.append((timestamps[i], empatica_data[i]))
    ts = traces.TimeSeries(data)
    interp_data = ts.sample(
        sampling_period=1.0 / float(sampling_rate),
        start=timestamps[0],
        end=timestamps[-1],
        interpolate='linear',
    )
    new_timestamps, new_data = map(list, zip(*interp_data))
    return new_data, new_timestamps


def process_e4_data(file, output_dir, time_period):
    with open(file, 'r') as f:
        json_file = json.load(f)
    e4_data = json_file['E4 Data']
    if e4_data:
        freq = json_file['KSF']['Frequency']
        freq_header = []
        for f_key in freq:
            freq_header.append(f_key[1])
        dur = json_file['KSF']['Duration']
        dur_header = []
        for d_key in dur:
            dur_header.append(d_key[1])
        ppg_file = open(os.path.join(output_dir, f"{pathlib.Path(file).stem}_HR.csv"), 'w',
                        newline='')
        eda_file = open(os.path.join(output_dir, f"{pathlib.Path(file).stem}_EDA.csv"), 'w',
                        newline='')
        acc_x_file = open(os.path.join(output_dir, f"{pathlib.Path(file).stem}_ACCX.csv"), 'w',
                          newline='')
        acc_y_file = open(os.path.join(output_dir, f"{pathlib.Path(file).stem}_ACCY.csv"), 'w',
                          newline='')
        acc_z_file = open(os.path.join(output_dir, f"{pathlib.Path(file).stem}_ACCZ.csv"), 'w',
                          newline='')
        tmp_file = open(os.path.join(output_dir, f"{pathlib.Path(file).stem}_TMP.csv"), 'w',
                        newline='')
        full_file = open(os.path.join(output_dir, f"{pathlib.Path(file).stem}_ALL.csv"), 'w',
                         newline='')

        ksf_ppg_header = ['Session Time', 'E4 Time'] + freq_header + dur_header + ppg_header
        ppg_f = csv.writer(ppg_file)
        ppg_f.writerow(ksf_ppg_header)

        ksf_eda_header = ['Session Time', 'E4 Time'] + freq_header + dur_header + eda_header
        eda_f = csv.writer(eda_file)
        eda_f.writerow(ksf_eda_header)

        ksf_accx_header = ['Session Time', 'E4 Time'] + freq_header + dur_header + accx_header
        acc_x_f = csv.writer(acc_x_file)
        acc_x_f.writerow(ksf_accx_header)
        ksf_accy_header = ['Session Time', 'E4 Time'] + freq_header + dur_header + accy_header
        acc_y_f = csv.writer(acc_y_file)
        acc_y_f.writerow(ksf_accy_header)
        ksf_accz_header = ['Session Time', 'E4 Time'] + freq_header + dur_header + accz_header
        acc_z_f = csv.writer(acc_z_file)
        acc_z_f.writerow(ksf_accz_header)

        ksf_tmp_header = ['Session Time', 'E4 Time'] + freq_header + dur_header + tmp_header
        tmp_f = csv.writer(tmp_file)
        tmp_f.writerow(ksf_tmp_header)

        ksf_full_header = ['Session Time',
                           'E4 Time'] + freq_header + dur_header + ppg_header + eda_header + accx_header + accy_header + accz_header + tmp_header
        full_f = csv.writer(full_file)
        full_f.writerow(ksf_full_header)

        e4_data = json_file['E4 Data']
        event_history = json_file['Event History']
        if e4_data:
            if len(e4_data) > 19:
                start_time_datetime = convert_timezone(
                    datetime.strptime(json_file['Session Date'] + json_file['Session Start Time'], datetime_format))
                start_time = int(EmpaticaE4.get_unix_timestamp(start_time_datetime))
                end_time = int(start_time + int(json_file['Session Time']))
                e4_data = convert_legacy_e4_data(e4_data)
                convert_legacy_events_e4(event_history, start_time)
            else:
                start_time = int(json_file['Session Start Timestamp'])
                end_time = int(json_file['Session End Timestamp'])
            interpolate_e4_data(e4_data)
            convert_timestamps(e4_data)
            malformed_data = 0
            for i in range(start_time + int(time_period / 2), end_time, time_period):
                try:
                    data_time = i - int(time_period / 2)
                    session_time = data_time - start_time
                    data_range = (data_time, data_time + time_period)
                    print(
                        f"\r\tProcessing {datetime.fromtimestamp(data_range[0]).strftime('%H:%M:%S')} to {datetime.fromtimestamp(data_range[1]).strftime('%H:%M:%S')}",
                        end='')
                    timestamp_list = np.arange(*data_range)

                    ppg_csv_data = [session_time, data_time] + len(freq_header) * [0] + len(dur_header) * [0]
                    eda_csv_data = [session_time, data_time] + len(freq_header) * [0] + len(dur_header) * [0]
                    acc_x_csv_data = [session_time, data_time] + len(freq_header) * [0] + len(dur_header) * [0]
                    acc_y_csv_data = [session_time, data_time] + len(freq_header) * [0] + len(dur_header) * [0]
                    acc_z_csv_data = [session_time, data_time] + len(freq_header) * [0] + len(dur_header) * [0]
                    tmp_csv_data = [session_time, data_time] + len(freq_header) * [0] + len(dur_header) * [0]
                    full_csv_data = [session_time, data_time] + len(freq_header) * [0] + len(dur_header) * [0]

                    ppg_data_range = find_indices(e4_data[EmpaticaData.BVP_TIMESTAMPS], timestamp_list)
                    ppg_data = e4_data[EmpaticaData.BVP][ppg_data_range[0]:ppg_data_range[-1]]

                    eda_data_range = find_indices(e4_data[EmpaticaData.EDA_TIMESTAMPS], timestamp_list)
                    eda_data = e4_data[EmpaticaData.EDA][eda_data_range[0]:eda_data_range[-1]]

                    acc_data_range = find_indices(e4_data[EmpaticaData.ACC_TIMESTAMPS], timestamp_list)
                    acc_x_data = e4_data[EmpaticaData.ACC_X][acc_data_range[0]:acc_data_range[-1]]
                    acc_y_data = e4_data[EmpaticaData.ACC_Y][acc_data_range[0]:acc_data_range[-1]]
                    acc_z_data = e4_data[EmpaticaData.ACC_Z][acc_data_range[0]:acc_data_range[-1]]

                    tmp_data_range = find_indices(e4_data[EmpaticaData.TMP_TIMESTAMPS], timestamp_list)
                    tmp_data = e4_data[EmpaticaData.TMP][tmp_data_range[0]:tmp_data_range[-1]]

                    for event in event_history:
                        if type(event[1]) is list:
                            event_duration = np.arange(int(event[3][0]), int(event[3][1]))
                            if int(event[3][0]) in timestamp_list or int(event[3][1]) in timestamp_list:
                                for data in [ppg_csv_data, eda_csv_data, acc_x_csv_data, acc_y_csv_data, acc_z_csv_data,
                                             tmp_csv_data, full_csv_data]:
                                    data[dur_header.index(event[0]) + 2 + len(freq_header)] = 1
                            if i in event_duration:
                                for data in [ppg_csv_data, eda_csv_data, acc_x_csv_data, acc_y_csv_data, acc_z_csv_data,
                                             tmp_csv_data, full_csv_data]:
                                    data[dur_header.index(event[0]) + 2 + len(freq_header)] = 1
                        else:
                            if int(event[3]) in timestamp_list:
                                for data in [ppg_csv_data, eda_csv_data, acc_x_csv_data, acc_y_csv_data, acc_z_csv_data,
                                             tmp_csv_data, full_csv_data]:
                                    data[freq_header.index(event[0]) + 2] = 1
                    try:
                        ppg_signals, _ = nk.ppg_process(ppg_data, sampling_rate=64)
                        ppg_results = nk.ppg_analyze(ppg_signals, sampling_rate=64, analyses=['time'])
                        cleaned_ppg_results = np.array(ppg_results.values.ravel().tolist())
                        cleaned_ppg_results[np.where(np.isnan(cleaned_ppg_results))[0]] = 0
                        cleaned_ppg_results[np.where(np.isinf(cleaned_ppg_results))[0]] = 0
                        cleaned_ppg_results = list(cleaned_ppg_results)
                        ppg_csv_data.extend(cleaned_ppg_results)
                        full_csv_data.extend(cleaned_ppg_results)
                    except Exception as e:
                        malformed_data += 1
                        ppg_csv_data.extend([0] * len(ppg_header))
                        full_csv_data.extend([0] * len(ppg_header))
                    try:
                        cleaned_eda_results = []
                        r, t = __cvx_eda(eda_data, 1 / 4)
                        cleaned_eda_results.extend(float(v) for v in get_stats(eda_data).values())
                        cleaned_eda_results.extend(float(v) for v in get_stats(np.ravel(r)).values())
                        cleaned_eda_results.extend(float(v) for v in get_stats(np.ravel(t)).values())
                        cleaned_eda_results = np.array(cleaned_eda_results)
                        cleaned_eda_results[np.where(np.isnan(cleaned_eda_results))[0]] = 0
                        cleaned_eda_results[np.where(np.isinf(cleaned_eda_results))[0]] = 0
                        cleaned_eda_results = list(cleaned_eda_results)
                        eda_csv_data.extend(cleaned_eda_results)
                        full_csv_data.extend(cleaned_eda_results)
                    except Exception as e:
                        malformed_data += 1
                        eda_csv_data.extend([0] * len(eda_header))
                        full_csv_data.extend([0] * len(eda_header))
                    try:
                        acc_x_results = [float(v) for v in get_stats(acc_x_data).values()]
                        acc_x_results = np.array(acc_x_results)
                        acc_x_results[np.where(np.isnan(acc_x_results))[0]] = 0
                        acc_x_results[np.where(np.isinf(acc_x_results))[0]] = 0
                        acc_x_results = list(acc_x_results)
                        acc_x_csv_data.extend(acc_x_results)
                        full_csv_data.extend(acc_x_results)

                        acc_y_results = [float(v) for v in get_stats(acc_y_data).values()]
                        acc_y_results = np.array(acc_y_results)
                        acc_y_results[np.where(np.isnan(acc_y_results))[0]] = 0
                        acc_y_results[np.where(np.isinf(acc_y_results))[0]] = 0
                        acc_y_results = list(acc_y_results)
                        acc_y_csv_data.extend(acc_y_results)
                        full_csv_data.extend(acc_y_results)

                        acc_z_results = [float(v) for v in get_stats(acc_z_data).values()]
                        acc_z_results = np.array(acc_z_results)
                        acc_z_results[np.where(np.isnan(acc_z_results))[0]] = 0
                        acc_z_results[np.where(np.isinf(acc_z_results))[0]] = 0
                        acc_z_results = list(acc_z_results)
                        acc_z_csv_data.extend(acc_z_results)
                        full_csv_data.extend(acc_z_results)
                    except Exception as e:
                        malformed_data += 1
                        acc_x_csv_data.extend([0] * len(accx_header))
                        full_csv_data.extend([0] * len(accx_header))
                        acc_y_csv_data.extend([0] * len(accy_header))
                        full_csv_data.extend([0] * len(accy_header))
                        acc_z_csv_data.extend([0] * len(accz_header))
                        full_csv_data.extend([0] * len(accz_header))
                    try:
                        tmp_results = [float(v) for v in get_stats(tmp_data).values()]
                        tmp_results = np.array(tmp_results)
                        tmp_results[np.where(np.isnan(tmp_results))[0]] = 0
                        tmp_results[np.where(np.isinf(tmp_results))[0]] = 0
                        tmp_results = list(tmp_results)
                        tmp_csv_data.extend(tmp_results)
                        full_csv_data.extend(tmp_results)
                    except Exception as e:
                        malformed_data += 1
                        tmp_csv_data.extend([0] * len(tmp_header))
                        full_csv_data.extend([0] * len(tmp_header))
                except KeyError:
                    print(f"\tNo E4 data found in {file}")
                except Exception as e:
                    print(f"\tSomething went wrong with {file}: {str(e)}\n{str(e)}")
                finally:
                    eda_f.writerow(eda_csv_data)
                    ppg_f.writerow(ppg_csv_data)
                    acc_x_f.writerow(acc_x_csv_data)
                    acc_y_f.writerow(acc_y_csv_data)
                    acc_z_f.writerow(acc_z_csv_data)
                    tmp_f.writerow(tmp_csv_data)
                    full_f.writerow(full_csv_data)
            print("\n\tCompleted processing")
        else:
            print("\tNo E4 data in this session, continuing...")
        eda_file.close()
        ppg_file.close()
        acc_x_file.close()
        acc_y_file.close()
        acc_z_file.close()
        tmp_file.close()
        return True
    else:
        return False


def eda_custom_process(eda_signal, sampling_rate=4, method="neurokit"):
    # https://github.com/neuropsychology/NeuroKit/issues/554#issuecomment-958031898
    eda_signal = nk.signal_sanitize(eda_signal)

    # Series check for non-default index
    if type(eda_signal) is pd.Series and type(eda_signal.index) != pd.RangeIndex:
        eda_signal = eda_signal.reset_index(drop=True)

    # Preprocess
    eda_cleaned = eda_signal  # Add your custom cleaning module here or skip cleaning
    eda_decomposed = nk.eda_phasic(eda_cleaned, sampling_rate=sampling_rate)

    # Find peaks
    peak_signal, info = nk.eda_peaks(
        eda_decomposed["EDA_Phasic"].values,
        sampling_rate=sampling_rate,
        method=method,
        amplitude_min=0.1,
    )
    info['sampling_rate'] = sampling_rate  # Add sampling rate in dict info

    # Store
    signals = pd.DataFrame({"EDA_Raw": eda_signal, "EDA_Clean": eda_cleaned})
    signals = pd.concat([signals, eda_decomposed, peak_signal], axis=1)
    return signals, info
