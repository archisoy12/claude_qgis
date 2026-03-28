#!/bin/bash
# QGIS PyQGIS 환경 설정 스크립트 (Linux/Mac)

# QGIS 설치 경로 설정 (필요에 따라 변경)
QGIS_PREFIX=/usr

export QGIS_PREFIX_PATH=$QGIS_PREFIX
export LD_LIBRARY_PATH=$QGIS_PREFIX/lib:$LD_LIBRARY_PATH
export PYTHONPATH=$QGIS_PREFIX/share/qgis/python:$PYTHONPATH
export PYTHONPATH=$QGIS_PREFIX/share/qgis/python/plugins:$PYTHONPATH

echo "PyQGIS 환경이 설정되었습니다."
echo "QGIS_PREFIX_PATH=$QGIS_PREFIX_PATH"
echo "PYTHONPATH=$PYTHONPATH"
