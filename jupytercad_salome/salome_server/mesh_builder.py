from pathlib import Path
import salome
import os
import base64
from tempfile import NamedTemporaryFile
from salome.geom import geomBuilder
from salome.smesh import smeshBuilder

salome.salome_init_without_session()
geompy = geomBuilder.New()
smesh = smeshBuilder.New()


def build_mesh(brep_string: str, number_of_segment: int, jcad_path: str) -> str:
    if number_of_segment < 0:
        raise ValueError("Number of segment negative")

    content = ""
    brep_temp = NamedTemporaryFile(delete=False)
    with open(brep_temp.name, "w") as f:
        f.write(brep_string)
        f.seek(0)

    geometry = geompy.ImportBREP(brep_temp.name)
    mesh = smesh.Mesh(geometry)

    hypo = mesh.Tetrahedron(algo=smeshBuilder.NETGEN_1D2D3D)
    params = hypo.Parameters(smeshBuilder.SIMPLE)
    params.SetNumberOfSegments(number_of_segment)
    params.LengthFromEdges()
    params.LengthFromFaces()

    is_done = mesh.Compute()
    if not is_done:
        raise RuntimeError("Problem during mesh computation")
    if jcad_path:
        med_path = Path.cwd() / Path(jcad_path.replace(".jcad", ".med"))
        mesh.ExportMED(str(med_path), 1)
    stl_tmp = NamedTemporaryFile(suffix=".stl", delete=False)

    mesh.ExportSTL(stl_tmp.name, 0)  # O means exporting in binary format
    stl_tmp.seek(0)

    with open(stl_tmp.name, "rb") as f_obj:
        content = f_obj.read()
    try:
        os.remove(stl_tmp.name)
        os.remove(brep_temp.name)
    except Exception:
        pass
    base64_content = base64.b64encode(content).decode("utf8")
    return base64_content
