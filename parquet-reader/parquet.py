
from fastparquet import ParquetFile
import snappy


def snappy_decompress(data, uncompressed_size):
    return snappy.decompress(data)
pf = ParquetFile('/Users/gocamilo/Documents/projects/AR-arcos/codecommit/gigigo-prototype/part-00000-2c49d629-bd7a-4b92-a858-57d495ec19a8.c000.snappy.parquet') # filename includes .snappy.parquet extension
dff=pf.to_pandas()
print(dff.head(10))
print(list(dff.columns))

compression_opts = dict(method='zip', archive_name='out.csv')

dff.to_csv('out.zip', index=False, compression=compression_opts)
