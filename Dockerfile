FROM python
WORKDIR /nmfy
ADD . .
RUN pip install -r requirements.txt
CMD ["python", "app/main.py"]
