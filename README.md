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

## TaskConfig parameters

- `foundation_href`: HREF to registration foundation data file. [Required]
- `asset`:  Key to STAC Item Asset to register. [Required]
- `output_href`: A hack to move the CODEM output files to the same location specified by the `--output` option. Would be nice if the `--output` option was saved in `kwargs`, rather than popped off. [Required]
- `solve_scale`: One of many possible CODEM parameters. [Optional]
