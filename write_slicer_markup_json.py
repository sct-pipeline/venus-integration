import os

fname_out =sys.argv[1]
origin = [float(sys.argv[2]),float(sys.argv[3]),float(sys.argv[4])]
normal = [float(sys.argv[5]),float(sys.argv[6]),float(sys.argv[7])]
slicer.util.loadScene('slicer_data/2022-11-16-Scene.mrml')
input_Node = getNode("input-pointNormal-Plane-markup")
print(f'input plane normal: {input_Node.GetNormal()}')
print(f'input plane normal: {input_Node.GetOrigin()}')
print('\n')
input_Node.SetNormal(normal)
input_Node.SetOrigin(origin)
print('New plane values:')
print(f'new plane normal: {input_Node.GetNormal()}')
print(f'new plane origin: {input_Node.GetOrigin()}')
myStorageNode = input_Node.CreateDefaultStorageNode()

filename=f'{os.getcwd()}/output/{fname_out}'
print(f'filename: {filename}')
myStorageNode.SetFileName(filename)
myStorageNode.WriteData(input_Node)
myStorageNode.UnRegister(None)
sys.exit(0)