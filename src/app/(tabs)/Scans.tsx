import { useState, useCallback } from "react";
import { useFocusEffect } from "expo-router";
import { ScrollView, StyleSheet, Text } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import ScannedImage from "../components/ScannedImage";

// Shape of one scan as the backend's GET /scans returns it.
// (url is a temporary presigned S3 link the backend generates for the photo.)
type Scan = { url: string; date: string; time: string };

export default function Scans() {
    const [scans, setScans] = useState<Scan[]>([]);
    const SERVER = process.env.EXPO_PUBLIC_SERVER_URL;

    // ── How the backend connects to this screen ──────────────────────────────
    // useEffect runs once, right after the screen first renders ([] deps = mount).
    // Inside it we call the FastAPI backend at GET /scans. The backend reads the
    // saved photo keys from the database, turns each into a presigned S3 URL, and
    // returns them as JSON ({ scans: [{ url, date, time }, ...] }). We drop that
    // array into React state with setScans — and because state changed, React
    // re-renders the list below with the new data. So the data flow is:
    //   backend /scans  →  fetch()  →  setScans()  →  <ScrollView> re-renders
    useFocusEffect(useCallback(() => {
        if (!SERVER) return;                      // no server URL configured yet
        fetch(`${SERVER}/scans`)                  // 1. call the backend endpoint
            .then(r => r.json())                // 2. parse the JSON response
            .then(d => setScans(d.scans ?? [])) // 3. store it -> triggers re-render
            .catch(e => console.error("Failed to load scans:", e));
    }, [SERVER])); // empty deps → fetch only once when the page mounts
    // (Note: the presigned URLs expire after ~1h. Swapping useEffect for
    //  useFocusEffect would re-fetch fresh links every time you open this tab.)

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
