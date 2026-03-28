import os
import sys


def init_qgis(qgis_prefix_path=None):
    """
    QGIS 애플리케이션을 초기화합니다.

    :param qgis_prefix_path: QGIS 설치 경로 (예: /usr 또는 C:/OSGeo4W)
    :return: QgsApplication 인스턴스
    """
    try:
        from qgis.core import QgsApplication
    except ImportError:
        raise ImportError(
            "PyQGIS를 찾을 수 없습니다. QGIS가 설치되어 있고 "
            "PYTHONPATH에 PyQGIS 경로가 포함되어 있는지 확인하세요."
        )

    if qgis_prefix_path is None:
        qgis_prefix_path = os.environ.get("QGIS_PREFIX_PATH", "/usr")

    QgsApplication.setPrefixPath(qgis_prefix_path, True)
    app = QgsApplication([], False)
    app.initQgis()
    return app


def load_vector_layer(path, layer_name="layer"):
    """
    벡터 레이어를 불러옵니다.

    :param path: 파일 경로 또는 데이터 소스 URI
    :param layer_name: 레이어 이름
    :return: QgsVectorLayer 인스턴스
    """
    from qgis.core import QgsVectorLayer

    layer = QgsVectorLayer(path, layer_name, "ogr")
    if not layer.isValid():
        raise ValueError(f"레이어를 불러올 수 없습니다: {path}")
    return layer


def load_raster_layer(path, layer_name="raster"):
    """
    래스터 레이어를 불러옵니다.

    :param path: 파일 경로
    :param layer_name: 레이어 이름
    :return: QgsRasterLayer 인스턴스
    """
    from qgis.core import QgsRasterLayer

    layer = QgsRasterLayer(path, layer_name)
    if not layer.isValid():
        raise ValueError(f"래스터 레이어를 불러올 수 없습니다: {path}")
    return layer


def connect_postgis(host, port, database, username, password, schema="public", table=None):
    """
    PostGIS 데이터베이스에 연결하여 벡터 레이어를 반환합니다.

    :param host: 데이터베이스 호스트
    :param port: 포트 번호 (기본값: 5432)
    :param database: 데이터베이스 이름
    :param username: 사용자 이름
    :param password: 비밀번호
    :param schema: 스키마 이름 (기본값: public)
    :param table: 테이블 이름 (None이면 URI만 반환)
    :return: QgsVectorLayer 인스턴스 또는 URI 문자열
    """
    from qgis.core import QgsDataSourceUri, QgsVectorLayer

    uri = QgsDataSourceUri()
    uri.setConnection(host, str(port), database, username, password)

    if table:
        uri.setDataSource(schema, table, "geom")
        layer = QgsVectorLayer(uri.uri(), table, "postgres")
        if not layer.isValid():
            raise ValueError(
                f"PostGIS 연결 실패: {host}:{port}/{database} - {schema}.{table}"
            )
        return layer

    return uri


def get_layer_info(layer):
    """
    레이어 기본 정보를 딕셔너리로 반환합니다.

    :param layer: QgsMapLayer 인스턴스
    :return: 레이어 정보 딕셔너리
    """
    info = {
        "name": layer.name(),
        "crs": layer.crs().authid(),
        "extent": layer.extent().toString(),
    }

    try:
        # 벡터 레이어 추가 정보
        info["feature_count"] = layer.featureCount()
        info["fields"] = [field.name() for field in layer.fields()]
    except AttributeError:
        # 래스터 레이어
        info["width"] = layer.width()
        info["height"] = layer.height()

    return info


def cleanup_qgis(app):
    """
    QGIS 애플리케이션을 종료하고 리소스를 해제합니다.

    :param app: QgsApplication 인스턴스
    """
    app.exitQgis()


if __name__ == "__main__":
    # 사용 예시
    app = init_qgis()
    print("QGIS 초기화 완료")

    # 벡터 레이어 예시 (파일 경로를 실제 경로로 변경하세요)
    # layer = load_vector_layer("/path/to/shapefile.shp", "my_layer")
    # print(get_layer_info(layer))

    # PostGIS 연결 예시
    # layer = connect_postgis(
    #     host="localhost",
    #     port=5432,
    #     database="mydb",
    #     username="user",
    #     password="password",
    #     schema="public",
    #     table="my_table",
    # )
    # print(get_layer_info(layer))

    cleanup_qgis(app)
    print("QGIS 종료 완료")
