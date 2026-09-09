# EID credential artwork

A dedicated identity credential for the EID homepage: machined titanium chassis, anodized cobalt layers, graphite face, raised lettering and warm alloy chip contacts. Created in Blender 5.2.1 LTS.

`eid-credential.blend` is the editable source. `build_credential.py` rebuilds the scene, renders a transparent PNG and exports GLB into this directory:

```sh
blender --background --python design/eid-credential/build_credential.py
```

The homepage uses the Blender-rendered PNG at `static/images/eid-credential.png` to keep the initial load lightweight and avoid requiring WebGL for authentication. Membership cards continue to use the existing level-specific card assets supplied by the backend.

Preview-generated member names and sample applications are not part of the production templates.
