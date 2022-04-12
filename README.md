<br />
<div align="center">
  <a href="https://github.com/Munroe-Meyer-Institute-VR-Laboratory/cometrics">
    <img src="images/cometrics_logo.png" alt="Logo" width="572" height="100">
  </a>
	<p align="center">
    cometrics is a Windows-based computer program that allows for the real-time coregistration of frequency- and duration-based behavior metrics, physiological signals from an Empatica E4, and video data.
	  <br />
	  <a href="https://github.com/Munroe-Meyer-Institute-VR-Laboratory/cometrics"><strong>Explore the docs »</strong></a>

[![Download cometrics](https://img.shields.io/badge/download-cometrics.msi-blue?style=for-the-badge)](https://github.com/Munroe-Meyer-Institute-VR-Laboratory/cometrics/releases/download/v1.0.6/cometrics-1.0.6-win64.msi)
	  <br />
	  <a href="https://github.com/Munroe-Meyer-Institute-VR-Laboratory/cometrics/issues">Report Bug</a>
	  ·
	  <a href="https://github.com/Munroe-Meyer-Institute-VR-Laboratory/cometrics/issues">Request Feature</a>
  </p>
</div>


<p align = center>
	<a href="https://github.com/Munroe-Meyer-Institute-VR-Laboratory/cometrics/graphs/contributors">
		<img src="https://img.shields.io/github/contributors/Munroe-Meyer-Institute-VR-Laboratory/cometrics.svg?style=flat-square" alt="Contributors" />
	</a>
	<a href="https://github.com/Munroe-Meyer-Institute-VR-Laboratory/cometrics/network/members">
		<img src="https://img.shields.io/github/forks/Munroe-Meyer-Institute-VR-Laboratory/cometrics.svg?style=flat-square" alt="Forks" />
	</a>
	<a href="https://github.com/Munroe-Meyer-Institute-VR-Laboratory/cometrics/stargazers">
		<img src="https://img.shields.io/github/stars/Munroe-Meyer-Institute-VR-Laboratory/cometrics.svg?style=flat-squarem/huskeee/tkvideo/network/members" alt="Stargazers"
		     />
	</a>
	<a href="https://github.com/Munroe-Meyer-Institute-VR-Laboratory/cometrics/issues">
		<img src="https://img.shields.io/github/issues/Munroe-Meyer-Institute-VR-Laboratory/cometrics.svg?style=flat-square" alt="Issues" />
	</a>
	<a href="https://github.com/Munroe-Meyer-Institute-VR-Laboratory/cometrics/blob/master/LICENSE">
		<img src="https://img.shields.io/github/license/Munroe-Meyer-Institute-VR-Laboratory/cometrics.svg?style=flat-square" alt="MIT License" />
	</a>
</p>

# Introduction 
cometrics has been designed to integrate directly into the workflow of the Severe Behavior Department at the Munroe-Meyer Institute in the University of Nebraska Medical Center, while simplifying multiple manual steps into a few mouse clicks.  By using a tracker spreadsheet, a patient's entire history can be collected into a single document from the software with your own specified graphs and format within that spreadsheet.  You can find an example of a tracker spreadsheet [here](https://github.com/Munroe-Meyer-Institute-VR-Laboratory/cometrics/blob/main/reference/Reference_Tracker.xlsx).  

## License
Distributed under the MIT License. See the [LICENSE](https://github.com/Munroe-Meyer-Institute-VR-Laboratory/cometrics/blob/main/LICENSE) file for more information.

## Roadmap
Starting from v1.0.5, we are looking to implement the following features in no particular order:
- [ ] Loading in previously recorded session data for editing when the session number already exists
- [ ] Export of E4 data into some human readable format
- [ ] Support of other research instruments such as a split belt treadmill

## Bug Reporting
When cometrics encounters an error, it is automatically logged and sent to us via Bugsnag.  To report a bug manually, please open an issue in the main repository [here](https://github.com/Munroe-Meyer-Institute-VR-Laboratory/cometrics/issues) and follow the instructions in the [user guide](https://github.com/Munroe-Meyer-Institute-VR-Laboratory/cometrics/blob/main/reference/Cometrics%20User%20Guide.pdf).

[<img alt="Bugsnag Logo" src="gui_images/bugsnag.png" />](https://www.bugsnag.com)

## Getting Started
### Clinicians and Researchers
The latest compiled binaries for the Windows platform can be found in the [Releases](https://github.com/Munroe-Meyer-Institute-VR-Laboratory/cometrics/releases) section of the repository.  To install the program on your system download the latest zip archive release to your system, unzip it in the directory of your choice, and double click `cometrics.exe` to start the program.  The logs directory will be created in your `C:` drive and the `config.yml` file will update with your system parameters.  To uninstall the program, simply delete the root folder of the software.  If you run into any issues, please make a report in the [Issues](https://github.com/Munroe-Meyer-Institute-VR-Laboratory/cometrics/issues) section of the repository and a maintainer will address the problem and help you get started.

### Developers
 * Clone the repo and install the module in developer mode
```sh
git clone https://github.com/Munroe-Meyer-Institute-VR-Laboratory/cometrics.git
python ./cometrics/setup.py develop
```
The codebase is built using Python 3.8 and the IDE used is PyCharm.

## Contribute
Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

