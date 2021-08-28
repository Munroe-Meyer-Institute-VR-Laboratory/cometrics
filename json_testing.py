import json


x = '{ "Name":"John Smith", "Age":13, "MRN":1}'
y = json.loads(x)

with open(y["Name"] + '.json', 'w') as f:
    json.dump(y, f)

file = open(y["Name"] + '.json')
patient = json.load(file)

print(patient["Name"])

x = '{ "Name":"Protocol 1", "Hair Pulling":"a", "Hair Pulling SB":"b"}'
y = json.loads(x)

with open(y["Name"] + '.json', 'w') as f:
    json.dump(y, f)


