import bpy, math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
def mat(name,h,metal,rough):
 c=[int(h[i:i+2],16)/255 for i in (0,2,4)];c=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in c]
 m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True
 m.node_tree.nodes.clear();p=m.node_tree.nodes.new('ShaderNodeBsdfPrincipled');out=m.node_tree.nodes.new('ShaderNodeOutputMaterial');m.node_tree.links.new(p.outputs['BSDF'],out.inputs['Surface']);p.inputs['Base Color'].default_value=(*c,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 return m
silver=mat('Machined titanium','B9C8D8',.92,.23)
edge=mat('Polished edge','EEF5FF',1,.17)
blue=mat('Anodized cobalt','0754E0',.8,.23)
navy=mat('Graphite core','122238',.8,.26)
light=mat('Frosted silver lettering','ECF8FF',.8,.25)
copper=mat('Warm alloy contacts','C6A46C',.82,.27)
objs=[]
def box(name,loc,dim,ma,bevel=.03):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=dim;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 o.data.materials.append(ma);mod=o.modifiers.new('Precision radius','BEVEL');mod.width=bevel;mod.segments=6;o.modifiers.new('Surface normals','WEIGHTED_NORMAL');objs.append(o);return o
def txt(name,value,loc,size,ma,spacing=1):
 cu=bpy.data.curves.new(name,'FONT');cu.body=value;cu.size=size;cu.extrude=.001;cu.bevel_depth=.001;cu.space_character=spacing;o=bpy.data.objects.new(name,cu);bpy.context.collection.objects.link(o);o.location=loc;cu.materials.append(ma);objs.append(o);return o
# Complete rear credential, offset from the foreground body.
box('Rear cobalt credential',(.18,.26,-.27),(3.34,2.12,.13),blue,.13)
box('Rear silver seam',(.18,.26,-.185),(3.23,2.01,.028),silver,.10)
# Foreground titanium chassis and multilayer face, all physically supported.
box('Solid titanium chassis',(0,0,-.03),(3.28,2.04,.25),silver,.14)
box('Graphite isolation seam',(0,0,.104),(3.15,1.91,.025),navy,.11)
box('Polished perimeter',(0,0,.123),(3.10,1.86,.024),edge,.10)
box('Cobalt front shell',(0,0,.153),(3.04,1.80,.06),blue,.095)
box('Satin central face',(-.05,0,.192),(2.91,1.68,.025),navy,.08)
# A broad blue panel, clearly different from a plain white template.
box('Blue identity band',(1.03,0,.214),(.60,1.65,.03),blue,.06)
for i in range(9): box('Precision edge slot %02d'%i,(1.22,-.62+i*.155,.235),(.09,.038,.007),silver,.009)
txt('Raised identity letters','EID',(-1.27,.04,.214),.53,light,1.10)
txt('Edition label','E ERA / IDENTITY',(-1.27,.62,.215),.092,silver,1.15)
txt('Member label','MEMBER',(-.54,-.47,.215),.085,silver,1.15)
txt('Serial etching','E - 0 0 1',(-.54,-.65,.216),.09,light)
# Embedded contact chip with framed and separated metal pads.
box('Chip socket',(-1.03,-.50,.218),(.45,.40,.014),navy,.035)
box('Chip surround',(-1.03,-.50,.23),(.41,.36,.014),copper,.028)
for row in range(3):
 for col in range(2):box('Contact pad %d-%d'%(row,col),(-1.14+col*.22,-.62+row*.12,.241),(.18,.087,.01),silver,.016)
# Tiny screws, service seam, and edge machining: all attached to the credential.
for x,y in [(-1.39,.70),(-1.39,-.72),(1.37,.70),(1.37,-.72)]:
 bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=.022,depth=.014,location=(x,y,.24));o=bpy.context.object;o.data.materials.append(edge);objs.append(o)
 box('Fastener slot',(x,y,.249),(.023,.005,.004),navy,.001)
for i in range(3):box('Side copper contacts %d'%i,(-.40+i*.25,-1.015,-.025),(.13,.012,.060),copper,.015)
# Physical raised rails on the exposed rear layer.
for i in range(5): box('Rear stepped spine %d'%i,(-1.0+i*.47,1.23,-.187),(.29,.045,.020),edge,.015)
# Orient the complete assembly rather than distorting individual parts.
root=bpy.data.objects.new('EID credential assembly',None);bpy.context.collection.objects.link(root)
for o in objs:o.parent=root
root.rotation_euler=(math.radians(8),math.radians(-8),math.radians(-13))
world=bpy.data.worlds.new('Neutral studio');bpy.context.scene.world=world;world.use_nodes=True;world.node_tree.nodes.clear();bg=world.node_tree.nodes.new('ShaderNodeBackground');wo=world.node_tree.nodes.new('ShaderNodeOutputWorld');world.node_tree.links.new(bg.outputs[0],wo.inputs[0]);bg.inputs[0].default_value=(.67,.75,.92,1);bg.inputs[1].default_value=.35
for name,loc,power,size,color in [('Large softbox',(-3,-2,7),650,4,(1,1,1)),('Blue rim',(3,3,5),850,3,(.48,.66,1)),('Long reflection',(4,-4,3),400,2,(1,.93,.82))]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.size=size;o.data.color=color;o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(3.4,-5.2,7.7));cam=bpy.context.object;cam.rotation_euler=(Vector((0,.07,0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=4.7
s=bpy.context.scene;s.camera=cam;s.render.engine='CYCLES';s.cycles.samples=64;s.cycles.use_denoising=True;s.render.film_transparent=True;s.render.resolution_x=1000;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.render.image_settings.color_mode='RGBA';s.render.filepath=str(ROOT/'eid-credential.png')
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'eid-credential.blend'));bpy.ops.render.render(write_still=True)
for o in bpy.context.selected_objects:o.select_set(False)
for o in objs:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(ROOT/'eid-credential.glb'),export_format='GLB',use_selection=True,export_apply=True)
