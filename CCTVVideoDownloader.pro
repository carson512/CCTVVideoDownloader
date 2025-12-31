QT       += core gui network widgets
TARGET = CCTVVideoDownloader
TEMPLATE = app
CONFIG += c++17

SOURCES += \
    src/source/about.cpp \
    src/source/apiservice.cpp \
    src/source/cctvvideodownloader.cpp \
    src/source/concat.cpp \
    src/source/concatworker.cpp \
    src/source/config.cpp \
    src/source/decrypt.cpp \
    src/source/decryptworker.cpp \
    src/source/downloaddialog.cpp \
    src/source/downloadengine.cpp \
    src/source/downloadmodel.cpp \
    src/source/downloadtask.cpp \
    src/source/import.cpp \
    src/source/logger.cpp \
    src/source/main.cpp \
    src/source/setting.cpp \
    src/source/tsmerger.cpp

HEADERS += \
    src/head/about.h \
    src/head/apiservice.h \
    src/head/cctvvideodownloader.h \
    src/head/concat.h \
    src/head/concatworker.h \
    src/head/config.h \
    src/head/decrypt.h \
    src/head/decryptworker.h \
    src/head/downloaddialog.h \
    src/head/downloadengine.h \
    src/head/downloadmodel.h \
    src/head/downloadtask.h \
    src/head/import.h \
    src/head/logger.h \
    src/head/setting.h \
    src/head/tsmerger.h \
    src/head/resource.h

FORMS += \
    src/ui/about.ui \
    src/ui/cctvvideodownloader.ui \
    src/ui/ctvd.ui \
    src/ui/ctvd_setting.ui \
    src/ui/dialog.ui \
    src/ui/import.ui \
    src/ui/process.ui

RESOURCES += \
    src/resources/cctvvideodownloader.qrc \
    src/resources/resources.qrc

RC_FILE = src/resources/CCTVVideoDownloader.rc

INCLUDEPATH += src/head src/decrypt

win32 {
    # Read VCPKG_PATH from environment variable
    VCPKG_ROOT = $$(VCPKG_PATH)
    !isEmpty(VCPKG_ROOT) {
        message("Using VCPKG_PATH: $$VCPKG_ROOT")
        INCLUDEPATH += $$VCPKG_ROOT/include
        LIBS += -L$$VCPKG_ROOT/lib
    }
    
    # Link dependencies
    LIBS += -lcpr -llibcurl -llibssl -llibcrypto -lws2_32 -lwldap32 -lcrypt32
}
