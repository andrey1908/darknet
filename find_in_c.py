import os
import sys

content_to_find = sys.argv[1]
folder = './src'
file_names = os.listdir(folder)
for file_name in file_names:
    if not file_name.endswith('.c'):
        continue
    with open(os.path.join(folder, file_name), 'r') as f:
        content = f.read()
    if content.find(content_to_find) != -1:
        print(file_name)

