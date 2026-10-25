"""Prepare the small official Zensus 2022 sample. Authoring only: requires pyproj.

Usage: python tools/prepare_population.py --archive /path/to/Zensus2022_Bevoelkerungszahl.zip
Students use the prepared CSV and need no projection or GIS Python libraries.
"""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import zipfile

from pyproj import Transformer

ROOT=Path(__file__).resolve().parents[1]
SOURCE='https://www.destatis.de/static/DE/zensus/gitterdaten/Zensus2022_Bevoelkerungszahl.zip'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',type=Path,required=True)
    args=parser.parse_args()
    west,south,east,north=13.18,52.40,13.60,52.62
    project=Transformer.from_crs(4326,3035,always_xy=True)
    inverse=Transformer.from_crs(3035,4326,always_xy=True)
    corners=[project.transform(x,y) for x in (west,east) for y in (south,north)]
    minx,maxx=min(x for x,y in corners)-1000,max(x for x,y in corners)+1000
    miny,maxy=min(y for x,y in corners)-1000,max(y for x,y in corners)+1000
    rows=[]
    with zipfile.ZipFile(args.archive) as z:
        member='Zensus2022_Bevoelkerungszahl_1km-Gitter.csv'
        with io.TextIOWrapper(z.open(member),encoding='utf-8-sig') as f:
            for row in csv.DictReader(f,delimiter=';'):
                x,y=float(row['x_mp_1km']),float(row['y_mp_1km'])
                if not minx<=x<=maxx or not miny<=y<=maxy:continue
                lon,lat=inverse.transform(x,y)
                value=int(row['Einwohner'])
                if west<=lon<=east and south<=lat<=north and value>0:
                    rows.append(dict(cell_id=row['GITTER_ID_1km'],longitude=round(lon,7),latitude=round(lat,7),
                                     population=value,reference_date='2022-05-15'))
    rows.sort(key=lambda r:(r['latitude'],r['longitude']))
    target=ROOT/'data/berlin_population_1km.csv'
    with target.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,lineterminator='\n',fieldnames=['cell_id','longitude','latitude','population','reference_date'])
        writer.writeheader();writer.writerows(rows)
    metadata={
        'title':'Zensus 2022 population, 1 km grid, rectangular Berlin study area',
        'source_url':SOURCE,'archive_member':member,
        'archive_sha256':hashlib.sha256(args.archive.read_bytes()).hexdigest(),
        'source_page':'https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Bevoelkerung/Zensus2022/_publikationen.html',
        'source_credit':'© Statistische Ämter des Bundes und der Länder, 2024',
        'license':'Datenlizenz Deutschland – Namensnennung – Version 2.0 (dl-de/by-2-0)',
        'license_url':'https://www.govdata.de/dl-de/by-2-0',
        'reference_date':'2022-05-15','retrieved':'2026-10-25','grid_cell_size_m':1000,
        'original_crs':'EPSG:3035','output_crs':'EPSG:4326',
        'bbox_wgs84':[west,south,east,north],'clip_rule':'Keep positive published counts whose cell centres fall inside this rectangle.',
        'cell_count':len(rows),'maximum_population':max(r['population'] for r in rows),
        'sum_of_published_counts':sum(r['population'] for r in rows),
        'modifications':'Rectangular subset; cell centres reprojected to WGS84; columns renamed; counts unchanged.',
        'limitations':['This rectangle is not the Berlin administrative boundary; its sum is not a Berlin city total.',
                      'Counts are reference-date census figures with Cell-Key confidentiality perturbation, not current or exact individual locations.',
                      'Uninhabited or unpublished cells are absent from the source. Absence is not a measured zero.',
                      'Display bar widths and heights are thematic encodings, not real building dimensions.']}
    (ROOT/'data/berlin_population_1km.metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2))
    print(f'Prepared {len(rows)} published 1-km cells; maximum {metadata["maximum_population"]}; sum {metadata["sum_of_published_counts"]}.')


if __name__=='__main__':main()
