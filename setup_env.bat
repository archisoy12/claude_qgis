@echo off
REM QGIS PyQGIS 환경 설정 스크립트 (Windows OSGeo4W)

REM OSGeo4W 설치 경로 설정 (필요에 따라 변경)
set OSGEO4W_ROOT=C:\OSGeo4W

call "%OSGEO4W_ROOT%\bin\o4w_env.bat"
call "%OSGEO4W_ROOT%\bin\qt5_env.bat"
call "%OSGEO4W_ROOT%\bin\py3_env.bat"

set QGIS_PREFIX_PATH=%OSGEO4W_ROOT%\apps\qgis
set PATH=%QGIS_PREFIX_PATH%\bin;%PATH%
set PYTHONPATH=%QGIS_PREFIX_PATH%\python;%PYTHONPATH%
set PYTHONPATH=%OSGEO4W_ROOT%\apps\qgis\python\plugins;%PYTHONPATH%

echo PyQGIS 환경이 설정되었습니다.
echo QGIS_PREFIX_PATH=%QGIS_PREFIX_PATH%
