# Load Packages
import sys
import os
import json

class pointNormalPlane(object):
    """
    Class to represent point-Normal plane (that can be written to and from a .json file)

    :param origin: list [x,y,z] with origin coordinates (float or int)
    :param normal: list [a,b,c] with normal components (float or int)
    :param orientation: 3-character string (e.g. 'RAS','LPS','LPI')
    :param filename: string ending in .json
    :param space: 'SCT_image' or 'anatomical'
    """
    def __init__(self,origin,normal,orientation,space='SCT_image'):
        self.origin = origin
        self.normal = normal
        self.orientation = orientation
        self.space = space

    @classmethod
    def fromJsonFile(cls,filename):
        with open(filename, "r") as f:
            data=f.read()
        dict_tmp=json.loads(data)
        return(pointNormalPlane(origin=dict_tmp['origin'],normal=dict_tmp['normal'],orientation=dict_tmp['orientation'],space=dict_tmp['space']))

    def write_plane_json(self,filename):
        new_plane_dict_json = json.dumps(self.__dict__)
        if (filename.endswith('json')):
            with open(filename, "w") as f:
                f.write(new_plane_dict_json)
        else:
            with open(f'{filename}.json', "w") as f:
                f.write(new_plane_dict_json)

fname_in = sys.argv[1]
plane = pointNormalPlane.fromJsonFile(sys.argv[1])
print(plane.normal)
print(plane.origin)
slicer.util.loadScene('../../../slicer_data/2022-11-16-Scene.mrml')
input_Node = getNode("input-pointNormal-Plane-markup")

print(f'input plane normal: {input_Node.GetNormal()}')
print(f'input plane normal: {input_Node.GetOrigin()}')
print('\n')
input_Node.SetNormal(plane.normal)
input_Node.SetOrigin(plane.origin)
print('New plane values:')
print(f'new plane normal: {input_Node.GetNormal()}')
print(f'new plane origin: {input_Node.GetOrigin()}')
myStorageNode = input_Node.CreateDefaultStorageNode()

filename = f'markup_{fname_in}'
myStorageNode.SetFileName(filename)
myStorageNode.WriteData(input_Node)
myStorageNode.UnRegister(None)
sys.exit(0)
