## Example Output and Keystroke File Setup
Cometrics uses files called keystroke files (KSFs) to organize the associations between keystrokes and intended coded behaviors.  For instance, the key 'a' when pressed during a cometrics session would be encoded as 'hitting', if the KSF were to define it as such.  

For an example of a correctly formatted KSF, [click here](https://github.com/Munroe-Meyer-Institute-VR-Laboratory/cometrics/blob/tutorials/tutorials/example_output_ksf_intro/ML_Coding_KSF.xlsx).  This is a KSF is used for coding videos of severe behavior with the intention of training a machine learning model.  

One of cometrics main development goals was the ability to perform retroactive data analysis by coding recorded video, which was not possible using existing tools to any level of repeatable accuracy.  So cometrics has an embedded video viewer that enables consistency between computers, coders, and locations.  An clip from one of our coder training videos is embedded below to show the type of behaviors the above KSF is intended for.


https://user-images.githubusercontent.com/22334349/201445560-1c20887b-3555-4df9-88d4-a6a7d826866f.mp4


The full video is available [here](https://github.com/Munroe-Meyer-Institute-VR-Laboratory/cometrics/blob/tutorials/tutorials/example_output_ksf_intro/Video_12.mp4).  Once a video is coded and the session is ended, a session file is generated in JSON format.  The session file for Video_12 can be found [here](https://github.com/Munroe-Meyer-Institute-VR-Laboratory/cometrics/blob/tutorials/tutorials/example_output_ksf_intro/12aMLMar222022.json) and a readable CSV export of the same file can be found [here](https://github.com/Munroe-Meyer-Institute-VR-Laboratory/cometrics/blob/tutorials/tutorials/example_output_ksf_intro/12aMLMar222022.csv).  The session file is a JSON file with twenty-three fields that contain all session information, such as the keystroke file and patient information fields, which can be seen below.

```
{
	"Session Location": "a", 
	"Assessment Name": "a", 
	"Condition Name": "MLCODING", 
	"Primary Therapist": "a", 
	"Case Manager": "a", 
	"Session Therapist": "a", 
	"Data Recorder": "a", 
	"Primary Data": "Primary", 
	"Session Number": "12", 
	"Session Date": "March 22, 2022", 
	"Session Start Time": "13:55:32", 
	"Session Time": 300,
	"Pause Time": 0, 
    "Keystroke File": "Main Ml Coding", 
    "Video File": "video 12 -converted ptz.mp4", 
    "Event History": [
        ["kick_hit object", 12, 92, null], 
        ["kick_hit object", 12, 100, null], 
        ["kick_hit object", 13, 107, null], 
        ["grab_scratch", 15, 118, null], 
        ["biting", 18, 141, null], 
        ["hitting", 21, 169, null], 
        ["sib-head hit", 23, 183, null], 
        ["sib-head hit", 23, 187, null], 
        ["sib-head hit", 25, 199, null], 
        ["st-head swing", [34, 60], 477, null], 
        ["sib-head hit", 96, 765, null], 
        ["grab_scratch", 98, 781, null], 
        ["biting", 98, 786, null], 
        ["kick_hit object", 111, 889, null], 
        ["kick_hit object", 112, 897, null], 
        ["kick_hit object", 113, 905, null], 
        ["hitting", 122, 975, null], 
        ["hitting", 123, 981, null], 
        ["hitting", 123, 987, null], 
        ["hitting", 168, 1346, null],
        ["hitting", 169, 1352, null], 
        ["grab_scratch", 171, 1371, null], 
        ["biting", 172, 1373, null], 
        ["sib-head hit", 174, 1390, null], 
        ["sib-head hit", 175, 1396, null], 
        ["grab_scratch", 176, 1405, null], 
        ["biting", 176, 1409, null], 
        ["sib-head hit", 182, 1452, null], 
        ["sib-head hit", 182, 1456, null], 
        ["sib-head hit", 183, 1467, null], 
        ["st-head swing", [191, 211], 1688, null], 
        ["grab_scratch", 212, 1694, null], 
        ["grab_scratch", 217, 1733, null], 
        ["sib-head hit", 225, 1800, null], 
        ["sib-head hit", 226, 1805, null], 
        ["kick_hit object", 233, 1861, null], 
        ["st-head swing", [241, 265], 2123, null], 
        ["hitting", 276, 2210, null], 
        ["hitting", 277, 2216, null], 
        ["grab_scratch", 278, 2222, null], 
        ["sib-head hit", 282, 2252, null], 
        ["grab_scratch", 285, 2276, null], 
        ["biting", 285, 2279, null]
    ], 
    "E4 Data": [],
    "KSF": {
        "Name": "Main Ml Coding", 
        "Frequency": [
            ["a", "hitting"], 
            ["s", "kicking"], 
            ["d", "pushing"], 
            ["f", "grab_scratch"], 
            ["g", "head butting"], 
            ["j", "hair pulling"], 
            ["h", "biting"], 
            ["k", "choking"], 
            ["l", "sib-head bang"], 
            ["q", "sib-head hit"], 
            ["w", "sib-self-hit"], 
            ["e", "sib-biting"], 
            ["r", "sib-eye poke"], 
            ["t", "sib-body slam"], 
            ["y", "sib-hair pull"], 
            ["u", "sib-choking"],
            ["i", "sib-pinch_scratch"], 
            ["o", "throwing object"], 
            ["p", "kick_hit object"], 
            ["z", "flip furniture"], 
            ["n", "flop"], 
            ["9", "no bx"]
        ], 
        "Duration": [
            ["1", "st- rock"], 
            ["2", "st-hand flap"],
            ["3", "st-touch/tap"], 
            ["4", "st-head swing"], 
            ["5", "stereovox"]
        ], 
        "Conditions": [
            "MLCODING"
        ]
    }
}
```

The format of the KSF file is strict and the following rules are detailed below for easy reference using the above KSF as the example:
1. The 'Assessment' cell must consist of columns A, B, and C merged and placed on row 1,
2. The 'Client' cell must consist of columns A and B merged and be placed on row 2,
3. The 'Data Coll.' cell must consist of columns D and E merged and be placed on row 2,
4. The 'Session' cell must be placed in column A row 3,
5. The 'Cond.' cell must be placed in column B row 3,
6. The 'Date' cell must be placed in column C row 3,
7. The 'Therapist' cell must be placed in column D row 3,
8. The 'Primary' cell must be placed in column E row 3,
9. The 'Reliability' cell must be placed in column F row 3,
10. The 'Notes' cell must be placed in column H row 3,
11. The 'Sess. Dur.' cell must be placed in column I row 3,
12. The 'Session Data' cell must consist of all frequency and duration key columns merged and placed on row 1,
13. The 'Frequency' cell must consist of all frequency key columns merged and placed on row 2,
14. The 'Duration' cell must consist of all duration key columns merged and placed on row 2,
15. The column cells below the 'Frequency' cell in row 3 must be only the frequency keys,
16. The column cells below the 'Duration' cell in row 3 must be only the duration keys,
17. The column cells in row 4 below the frequency key cells must be the associated code for the key, i.e. 'a' is 'hitting',
18. The column cells in row 4 below the duration key cells must be the associated code for the key, i.e. '1' is 'st-rock',
19. The column after the duration key cells in row 3 must be 'ST',
20. The column cell in row 4 below 'ST' must be 'Session Time',
21. The column cell after the 'ST' cell must be 'PT',
22. The column in row 4 below 'PT' must be 'Pause Time'.

Only lowercase letters are accepted as key inputs and so only lowercase letters should be placed within the KSF.

This format is observed in the above KSF and in the [reference KSF](https://github.com/Munroe-Meyer-Institute-VR-Laboratory/cometrics/blob/tutorials/reference/Reference_Tracker.xlsx) packaged with cometrics.  There is only the need to modify the keys associated with your specific behaviors, so the main format breaking changes are adding keys and not expanding or contracting the 'Frequency', 'Duration', and 'Session Data' merged cells, which are 12, 13, and 14 in the above list.  Additionally, ensure that the 'Session Time' and 'Pause Time' cells are kept in their proper place next to the 'Duration' keys, steps 19, 20, 21, and 22 in the above list.
