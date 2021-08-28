import json


x = '{ "Name":"John Smith", "Age":13, "MRN":1}'
y = json.loads(x)

with open(y["Name"] + '.json', 'w') as f:
    json.dump(y, f)

file = open(y["Name"] + '.json')
patient = json.load(file)

print(patient["Name"])
