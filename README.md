# STAC Task for CODEM

## Install for development

Relying on pdal and gdal, so use a conda environment.

```shell
conda env create -f environment.yaml
conda activate codem-stactask
pip install -e .
pip install -r requirements-dev.txt
```

## Example

```shell
codem-stactask run --output examples/output/output-payload.json examples/input/input-payload.json
```

## Input payload

- The `features` list must contain a single AOI Item and a single foundation Item.
- Both Items must contain:
  - a `collection` field
  - a self `link`
  - a `codem:role` property, which must be "aoi" for the AOI Item and "fnd" for the foundation Item

## TaskConfig parameters

- `fnd_asset`: Foundation data asset key.
- `aoi_asset`: AOI data asset key.
- Optional codem parameters, e.g., `"codem:solve_scale": True`
