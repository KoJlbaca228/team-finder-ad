FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN addgroup --system django \
    && adduser --system --ingroup django django

COPY requirements.txt ./
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

COPY --chown=django:django . .

RUN mkdir -p media staticfiles \
    && chown -R django:django media staticfiles

USER django

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
