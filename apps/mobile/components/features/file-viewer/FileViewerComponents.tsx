import { useState } from "react"
import useFileURL from "@hooks/useFileURL"
import { getFileExtension, isImageFile, isVideoFile } from "@raven/lib/utils/operations"
import WebView from "react-native-webview"
import { WebViewSourceUri } from "react-native-webview/lib/WebViewTypes"
import { useVideoPlayer, VideoView } from 'expo-video'
import ErrorBanner from "@components/common/ErrorBanner";
import { router } from "expo-router";
import { useWindowDimensions, View } from "react-native";
import { fitContainer, ResumableZoom, Source, useImageResolution } from "react-native-zoom-toolkit";
import { Image } from "expo-image";
//// Neoffice - mobile i18n (e9ee1845e, 2026-01-04 "feat(mobile): Add internationalization (i18n)
//// support"). Upstream hardcodes every screen string in English; our customers are French-speaking
//// (Suisse romande), so the app ships FR+EN through react-i18next - setup in apps/mobile/lib/i18n.ts,
//// catalogues in apps/mobile/locales/{en,fr}.json, picker in app/[site_id]/(tabs)/profile/language.tsx.
import { useTranslation } from "react-i18next";


export const useFileViewerAttributes = (uri: string) => {
    const fileExtension = getFileExtension(uri)
    const isVideo = isVideoFile(fileExtension)
    const isImage = isImageFile(fileExtension)

    const [showHeader, setShowHeader] = useState(true)

    const handleShowHeader = () => {
        setShowHeader((prev) => !prev)
    }
    return { isVideo, isImage, fileExtension, showHeader, handleShowHeader }
}

export const RenderFile = ({ uri, handleShowHeader, isVideo, isImage }: { uri: string, handleShowHeader: () => void, isVideo: boolean, isImage: boolean }) => {
    if (isVideo) {
        return <VideoPlayer uri={uri} />
    }
    else if (isImage) {
        return <ImageViewer uri={uri} handleShowHeader={handleShowHeader} />
    }
    return <FileView uri={uri} />

}

const FileView = ({ uri }: { uri: string }) => {
    const source = useFileURL(uri)

    return (
        <WebView
            source={source as WebViewSourceUri}
            style={{ flex: 1 }}
        />
    )
}

const VideoPlayer = ({ uri }: { uri: string }) => {

    const source = useFileURL(uri)

    const player = useVideoPlayer(source ?? {}, player => {
        player.loop = true
        player.play()
    })

    return (
        <VideoView player={player}
            allowsFullscreen
            style={
                {
                    width: '100%',
                    height: '100%',
                }
            } />
    )
}

interface ImageViewerProps {
    uri: string
    handleShowHeader: VoidFunction
}

const ImageViewer = ({ uri, handleShowHeader }: ImageViewerProps) => {
    //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): useTranslation() added to feed the t() calls below.
    const { t } = useTranslation()
    const source = useFileURL(uri)
    if (!source) {
        return <View className="p-2">
            {/* //// Neoffice - mobile i18n (e9ee1845e, 2026-01-04): English literal replaced by t(), FR in locales/fr.json. */}
            <ErrorBanner message={t('errors.somethingWentWrong')} heading={t('errors.couldNotOpenImage')} />
        </View>
    }
    return (
        <ImageComponent source={source} handleShowHeader={handleShowHeader} />
    )
}

export default ImageViewer

const ImageComponent = ({ source, handleShowHeader }: { source: Source, handleShowHeader: VoidFunction }) => {

    const { width, height } = useWindowDimensions()
    const { isFetching, resolution, error } = useImageResolution(source)
    if (isFetching || resolution === undefined || error) {
        return <View className="p-2">
            {error && <ErrorBanner message={error.message} />}
        </View>
    }

    const size = fitContainer(resolution.width / resolution.height, {
        width,
        height,
    })

    const backSwipe = (direction: string) => {
        if (direction === 'right') {
            router.back()
        }
    }

    return (
        <ResumableZoom extendGestures maxScale={resolution} onTap={handleShowHeader} onSwipe={backSwipe}>
            <Image source={source} style={{ ...size }} contentFit="contain" enableLiveTextInteraction />
        </ResumableZoom>
    )
}