# QGIS 연결 (PyQGIS)

Python에서 QGIS에 연결하여 지리 데이터를 처리하는 스크립트입니다.

## 사전 요구 사항

- QGIS 3.x 이상 설치
- PyQGIS (QGIS 설치 시 포함)

## 환경 설정

### Linux / Mac

```bash
source setup_env.sh
```

### Windows (OSGeo4W Shell)

```bat
setup_env.bat
```

## 사용법

```python
from qgis_connection import init_qgis, load_vector_layer, connect_postgis, get_layer_info, cleanup_qgis

# QGIS 초기화
app = init_qgis()

# 벡터 레이어 불러오기 (Shapefile)
layer = load_vector_layer("/path/to/file.shp", "my_layer")
print(get_layer_info(layer))

# PostGIS 연결
layer = connect_postgis(
    host="localhost",
    port=5432,
    database="mydb",
    username="user",
    password="password",
    schema="public",
    table="my_table",
)
print(get_layer_info(layer))

# 래스터 레이어 불러오기
from qgis_connection import load_raster_layer
raster = load_raster_layer("/path/to/file.tif", "my_raster")
print(get_layer_info(raster))

# 종료
cleanup_qgis(app)
```

## 주요 기능

| 함수 | 설명 |
|------|------|
| `init_qgis()` | QGIS 애플리케이션 초기화 |
| `load_vector_layer()` | Shapefile 등 벡터 레이어 로드 |
| `load_raster_layer()` | GeoTIFF 등 래스터 레이어 로드 |
| `connect_postgis()` | PostGIS 데이터베이스 연결 |
| `get_layer_info()` | 레이어 정보 조회 |
| `cleanup_qgis()` | QGIS 종료 및 리소스 해제 |
