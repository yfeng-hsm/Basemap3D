"""Execute the small notebook cells and regenerate the five HTML gallery pages."""
import json
import os
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def main():
    os.chdir(ROOT)
    notebook=json.loads((ROOT/"Mainz_3D_5_Tasks.ipynb").read_text(encoding="utf-8"))
    namespace={}
    for cell in notebook["cells"]:
        if cell["cell_type"]=="code":
            exec(compile("".join(cell["source"]),"notebook-cell","exec"),namespace)
    target=ROOT/"docs"/"examples"
    target.mkdir(parents=True,exist_ok=True)
    for file in sorted((ROOT/"results").glob("task*.html")):
        shutil.copyfile(file,target/file.name)
        print(f"Built {file.name}")
    return namespace


if __name__=="__main__":
    main()
