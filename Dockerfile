FROM continuumio/miniconda3

# Install missing cv2 dependency
RUN apt-get update
RUN apt-get install -y libgl1

# Create and activate the Conda environment
COPY environment.yml .
RUN conda env create -f environment.yml

# Automatically activate the conda environment
RUN echo "source activate codem-stactask" >> ~/.bashrc
ENV PATH /opt/conda/envs/codem-stactask/bin:$PATH

COPY src ./src
COPY pyproject.toml .
RUN pip install .

# ENTRYPOINT [ "codem-stactask" ]
