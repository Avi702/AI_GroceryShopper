import { Image, Text, View, StyleSheet } from "react-native";

interface ScannedImageProps {
    url: string;
    date: string;
    time: string;
}

export default function ScannedImage({ url, date, time }: ScannedImageProps) {
    return (
        <View style={styles.card}>
            <Image source={{ uri: url }} style={styles.image} />
            <View style={styles.meta}>
                <Text style={styles.metaText}>{date}</Text>
                <Text style={styles.metaText}>{time}</Text>
            </View>
        </View>
    );
}

const styles = StyleSheet.create({
    card: {
        width: "100%",          // each card spans the full screen width
        marginBottom: 16,
        backgroundColor: "#00003B",
    },
    image: {
        width: "100%",
        height: 240,
        backgroundColor: "#11224a", // shows while the photo loads
    },
    meta: {
        flexDirection: "row",
        justifyContent: "space-between",
        paddingHorizontal: 16,
        paddingVertical: 10,
    },
    metaText: {
        color: "#aaa",
        fontSize: 13,
    },
});
