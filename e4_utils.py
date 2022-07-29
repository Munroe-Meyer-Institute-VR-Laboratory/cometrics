import csv
import glob
import json
import os
import pathlib
import traceback
from datetime import datetime
from tkinter import messagebox
import neurokit2 as nk
import pandas as pd
import warnings
warnings.filterwarnings('ignore')


def export_e4_metrics(prim_dir, reli_dir, time_period=20):
    prim_files = glob.glob(f'{prim_dir}/**/*.json', recursive=True)
    reli_files = glob.glob(f'{reli_dir}/**/*.json', recursive=True)
    prim_filepaths = [_ for _ in prim_files if _.split("\\")[0]]
    reli_filepaths = [_ for _ in reli_files if _.split("\\")[0]]
    eda_header = ['SCR_Peaks_N', 'SCR_Peaks_Amplitude_Mean']
    ppg_header = ['PPG_Rate_Mean', 'HRV_MeanNN', 'HRV_SDNN', 'HRV_SDANN1', 'HRV_SDNNI1',
                  'HRV_SDANN2', 'HRV_SDNNI2', 'HRV_SDANN5', 'HRV_SDNNI5', 'HRV_RMSSD', 'HRV_SDSD', 'HRV_CVNN',
                  'HRV_CVSD', 'HRV_MedianNN', 'HRV_MadNN', 'HRV_MCVNN', 'HRV_IQRNN', 'HRV_Prc20NN', 'HRV_Prc80NN',
                  'HRV_pNN50', 'HRV_pNN20', 'HRV_MinNN', 'HRV_MaxNN', 'HRV_HTI', 'HRV_TINN', 'HRV_ULF', 'HRV_VLF',
                  'HRV_LF', 'HRV_HF', 'HRV_VHF', 'HRV_LFHF', 'HRV_LFn', 'HRV_HFn', 'HRV_LnHF', 'HRV_SD1', 'HRV_SD2',
                  'HRV_SD1SD2', 'HRV_S', 'HRV_CSI', 'HRV_CVI', 'HRV_CSI_Modified', 'HRV_PIP', 'HRV_IALS', 'HRV_PSS',
                  'HRV_PAS', 'HRV_GI', 'HRV_SI', 'HRV_AI', 'HRV_PI', 'HRV_C1d', 'HRV_C1a', 'HRV_SD1d', 'HRV_SD1a',
                  'HRV_C2d', 'HRV_C2a', 'HRV_SD2d', 'HRV_SD2a', 'HRV_Cd', 'HRV_Ca', 'HRV_SDNNd', 'HRV_SDNNa',
                  'HRV_DFA_alpha1', 'HRV_MFDFA_alpha1_Width', 'HRV_MFDFA_alpha1_Peak', 'HRV_MFDFA_alpha1_Mean',
                  'HRV_MFDFA_alpha1_Max', 'HRV_MFDFA_alpha1_Delta', 'HRV_MFDFA_alpha1_Asymmetry',
                  'HRV_MFDFA_alpha1_Fluctuation', 'HRV_MFDFA_alpha1_Increment', 'HRV_ApEn', 'HRV_SampEn', 'HRV_ShanEn',
                  'HRV_FuzzyEn', 'HRV_MSEn', 'HRV_CMSEn', 'HRV_RCMSEn', 'HRV_CD', 'HRV_HFD', 'HRV_KFD', 'HRV_LZC']

    if prim_filepaths and reli_filepaths:
        for file in prim_filepaths + reli_filepaths:
            with open(file, 'r') as f:
                json_file = json.load(f)
            freq = json_file['KSF']['Frequency']
            freq_header = []
            for f_key in freq:
                freq_header.append(f_key[1])
            dur = json_file['KSF']['Duration']
            dur_header = []
            for d_key in dur:
                dur_header.append(d_key[1])
            with open(os.path.join(pathlib.Path(file).parent, f"{pathlib.Path(file).stem}_HR.csv"), 'w', newline='') as ppg_file:
                ksf_ppg_header = ['Event Time', 'E4 Time'] + freq_header + dur_header + ppg_header
                ppg_f = csv.writer(ppg_file)
                ppg_f.writerow([pathlib.Path(file).parts[-3]])
                ppg_f.writerow([pathlib.Path(file).parts[-2]])
                ppg_f.writerow([pathlib.Path(file).stem])
                ppg_f.writerow([str(datetime.now())])
                ppg_f.writerow(ksf_ppg_header)

                with open(os.path.join(pathlib.Path(file).parent, f"{pathlib.Path(file).stem}_EDA.csv"), 'w', newline='') as eda_file:
                    ksf_eda_header = ['Event Time', 'E4 Time'] + freq_header + dur_header + eda_header
                    eda_f = csv.writer(eda_file)
                    eda_f.writerow([pathlib.Path(file).parts[-3]])
                    eda_f.writerow([pathlib.Path(file).parts[-2]])
                    eda_f.writerow([pathlib.Path(file).stem])
                    eda_f.writerow([str(datetime.now())])
                    eda_f.writerow(ksf_eda_header)

                    e4_data = json_file['E4 Data']
                    if e4_data:
                        if len(e4_data) > 19:
                            event_history = json_file['Event History']
                            for i in range(int(time_period / 2), len(e4_data), time_period):
                                try:
                                    data_time = i - int(time_period / 2)
                                    ppg_data, eda_data = [], []
                                    ppg_csv_data, eda_csv_data = [0, data_time] + len(freq_header) * [0] + len(
                                        dur_header) * [0], \
                                                                 [0, data_time] + len(freq_header) * [0] + len(
                                                                     dur_header) * [0]
                                    for d in e4_data[i - int(time_period / 2):i + int(time_period / 2)]:
                                        ppg_data.extend(d[5])
                                        eda_data.extend(d[7])
                                    for event in event_history:
                                        if type(event[1]) is list:
                                            if event[3] in list(
                                                    range(i - int(time_period / 2), i + int(time_period / 2))):
                                                ppg_csv_data[0] = event[1][1]
                                                eda_csv_data[0] = event[1][1]
                                                ppg_csv_data[dur_header.index(event[0]) + 2 + len(freq_header)] = 1
                                                eda_csv_data[dur_header.index(event[0]) + 2 + len(freq_header)] = 1
                                        else:
                                            if i - int(time_period / 2) <= event[3] < i + int(time_period / 2):
                                                ppg_csv_data[0] = event[1]
                                                eda_csv_data[0] = event[1]
                                                ppg_csv_data[freq_header.index(event[0]) + 2] = 1
                                                eda_csv_data[freq_header.index(event[0]) + 2] = 1

                                    ppg_signals, _ = nk.ppg_process(ppg_data, sampling_rate=64)
                                    ppg_results = nk.ppg_analyze(ppg_signals, sampling_rate=64)

                                    eda_signals, _ = eda_custom_process(eda_data, sampling_rate=4)
                                    eda_results = nk.eda_analyze(eda_signals, method='interval-related')

                                    eda_csv_data.extend(eda_results.values.ravel().tolist())
                                    eda_f.writerow(eda_csv_data)
                                    ppg_csv_data.extend(ppg_results.values.ravel().tolist())
                                    ppg_f.writerow(ppg_csv_data)
                                except KeyError:
                                    print(f"No E4 data found in {file}")
                                    continue
                                except Exception as e:
                                    print(f"Something went wrong with {file}: {str(e)}")
                                    continue
                        else:
                            event_history = json_file['Event History']
                            for i in range(int(time_period / 2), int(json_file['Session Time']), time_period):
                                try:
                                    data_time = i - int(time_period / 2)
                                    ppg_csv_data, eda_csv_data = [0, data_time] + len(freq_header) * [0] + len(
                                        dur_header) * [0], \
                                                                 [0, data_time] + len(freq_header) * [0] + len(
                                                                     dur_header) * [0]

                                    ppg_data = e4_data[5][data_time * 64:(data_time + time_period) * 64]
                                    eda_data = e4_data[7][data_time * 4:(data_time + time_period) * 4]

                                    for event in event_history:
                                        if type(event[1]) is list:
                                            if event[3] in list(
                                                    range(i - int(time_period / 2), i + int(time_period / 2))):
                                                ppg_csv_data[0] = event[1][1]
                                                eda_csv_data[0] = event[1][1]
                                                ppg_csv_data[dur_header.index(event[0]) + 2 + len(freq_header)] = 1
                                                eda_csv_data[dur_header.index(event[0]) + 2 + len(freq_header)] = 1
                                        else:
                                            if i - int(time_period / 2) <= event[1] < i + int(time_period / 2):
                                                ppg_csv_data[0] = event[1]
                                                eda_csv_data[0] = event[1]
                                                ppg_csv_data[freq_header.index(event[0]) + 2] = 1
                                                eda_csv_data[freq_header.index(event[0]) + 2] = 1

                                    ppg_signals, _ = nk.ppg_process(ppg_data, sampling_rate=64)
                                    ppg_results = nk.ppg_analyze(ppg_signals, sampling_rate=64)

                                    eda_signals, _ = eda_custom_process(eda_data, sampling_rate=4)
                                    eda_results = nk.eda_analyze(eda_signals, method='interval-related')

                                    eda_csv_data.extend(eda_results.values.ravel().tolist())
                                    eda_f.writerow(eda_csv_data)
                                    ppg_csv_data.extend(ppg_results.values.ravel().tolist())
                                    ppg_f.writerow(ppg_csv_data)
                                except KeyError:
                                    print(f"INFO: No E4 data found in {file}")
                                    break
                                except Exception as e:
                                    print(f"Something went wrong with {file}: {str(e)}")
                                    continue
        messagebox.showinfo("E4 Metrics Computed", "E4 sessions have been successfully analyzed!\n"
                                                   "Check in raw data folders for output CSV files.")
    else:
        messagebox.showwarning("Warning", "No E4 sessions found!")


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