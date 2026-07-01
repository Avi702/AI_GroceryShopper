import { useState, useCallback } from "react";
import { useFocusEffect } from "expo-router";
import { ScrollView, StyleSheet, Text } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import ScannedImage from "../components/ScannedImage";


type Scan = { url: string; date: string; time: string };

export default function Scans() {
    const [scans, setScans] = useState<Scan[]>([]);
    const SERVER = process.env.EXPO_PUBLIC_SERVER_URL;
    useFocusEffect(useCallback(() => {
        if (!SERVER) return;                    
        fetch(`${SERVER}/scans`)               
            .then(r => r.json())               
            .then(d => setScans(d.scans ?? []))
            .catch(e => console.error("Failed to load scans:", e));
    }, [SERVER]));

    return (
        <SafeAreaView style={styles.container}>
            <Text style={styles.header}>Scans</Text>
            <ScrollView contentContainerStyle={styles.list}>
                {scans.map((s, i) => (
                    <ScannedImage key={i} url={s.url} date={s.date} time={s.time} />
                ))}
            </ScrollView>
        </SafeAreaView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: "#00001B",
    },
    header: {
        color: "white",
        fontWeight: "bold",
        fontSize: 28,
        padding: 16,
    },
    list: {
        paddingBottom: 24,
    },
});
