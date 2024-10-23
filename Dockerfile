FROM jupyter/minimal-notebook


COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

USER ${NB_UID}
WORKDIR /home/jacopomanenti/algo/Privacy-Preserving-Algorithmic-Trading-with-Zero-Knowledge-Proofs
