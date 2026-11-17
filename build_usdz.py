# Converts models/*.glb into models_ios/*.usdz for iPhone AR Quick Look
import glob, os, numpy as np, trimesh
from pxr import Usd, UsdGeom, UsdShade, Sdf, Gf, Vt, UsdUtils
here=os.path.dirname(os.path.abspath(__file__))
for glb in sorted(glob.glob(f'{here}/models/*.glb')):
    key=os.path.basename(glb)[:-4]
    sc=trimesh.load(glb)
    usda=f'/tmp/{key}.usdc'
    st=Usd.Stage.CreateNew(usda)
    UsdGeom.SetStageUpAxis(st, UsdGeom.Tokens.y); UsdGeom.SetStageMetersPerUnit(st, 1.0)
    root=UsdGeom.Xform.Define(st,'/Molecule'); st.SetDefaultPrim(root.GetPrim())
    for i,g in enumerate(sc.dump()):
        g.fix_normals()
        p=f'/Molecule/part{i}'
        mesh=UsdGeom.Mesh.Define(st,p)
        mesh.CreatePointsAttr(Vt.Vec3fArray.FromNumpy(g.vertices.astype(np.float32)))
        mesh.CreateFaceVertexCountsAttr(Vt.IntArray([3]*len(g.faces)))
        mesh.CreateFaceVertexIndicesAttr(Vt.IntArray(g.faces.flatten().tolist()))
        mesh.CreateNormalsAttr(Vt.Vec3fArray.FromNumpy(g.vertex_normals.astype(np.float32)))
        mesh.SetNormalsInterpolation(UsdGeom.Tokens.vertex)
        mesh.CreateSubdivisionSchemeAttr(UsdGeom.Tokens.none)
        c=np.array(g.visual.material.baseColorFactor)/255.0
        lin=[(x/12.92 if x<=0.04045 else ((x+0.055)/1.055)**2.4) for x in c[:3]]  # sRGB -> linear
        m=UsdShade.Material.Define(st,p+'_mat')
        sh=UsdShade.Shader.Define(st,p+'_mat/PBR'); sh.CreateIdAttr('UsdPreviewSurface')
        sh.CreateInput('diffuseColor',Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*lin))
        sh.CreateInput('roughness',Sdf.ValueTypeNames.Float).Set(0.4)
        sh.CreateInput('metallic',Sdf.ValueTypeNames.Float).Set(0.0)
        if c[3]<1: sh.CreateInput('opacity',Sdf.ValueTypeNames.Float).Set(float(c[3]))
        m.CreateSurfaceOutput().ConnectToSource(sh.ConnectableAPI(),'surface')
        UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim()).Bind(m)
    st.GetRootLayer().Save()
    out=f'{here}/models_ios/{key}.usdz'
    if os.path.exists(out): os.remove(out)
    assert UsdUtils.CreateNewUsdzPackage(Sdf.AssetPath(usda), out)
    print(key, os.path.getsize(out))
