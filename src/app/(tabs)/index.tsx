import { ActivityIndicator, Alert, Image, Pressable, Text, View, StyleSheet, ScrollView } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import {router} from "expo-router"
import ReportCard from "../components/ReportCard";
import {useState, useEffect, useRef} from "react"
import * as ImagePicker from "expo-image-picker"
type InventoryItem = { name: string; image_url: string; confidence: number; amount: number; date: string; time: string };
type ScanResult = { inventory: { items: InventoryItem[]; reasoning: string }; shopping: any };

const fakeData: InventoryItem[] = [
  { name: "2% Milk", image_url: "https://images.unsplash.com/photo-1550583724-b2692b85b150", confidence: 0.95, amount: 3, date: "10/17/2025", time: "10:30 AM" },
]

export default function Index() {
  const [loading, isLoading] = useState(false)
  const [scanning, setScanning] = useState(false)   // true while waiting for the Pi's new scan
  const [result, setResult] = useState<ScanResult | null>(null)
  const prevSigRef = useRef("")
  const SERVER = process.env.EXPO_PUBLIC_SERVER_URL;
  const handleScan = async() => {
      if (!SERVER) {
          Alert.alert("No server URL", "EXPO_PUBLIC_SERVER_URL is not set. Restart `expo start` after editing .env.");
          return;
      }
      isLoading(true)
      try{
          const res = await fetch(`${SERVER}/request-scan`, { method: "POST" });
          if (!res.ok) throw new Error(`Server returned ${res.status}`);
          prevSigRef.current = JSON.stringify(result?.inventory?.items ?? [])
          setScanning(true)
          setTimeout(() => setScanning(false), 120000)
          Alert.alert("Scan requested", "The Raspberry Pi will take a picture shortly.");
      }catch(e){
          console.error("Scan request failed:", e);
          Alert.alert("Scan request failed", String(e));
      } finally {
          isLoading(false);
      }
  }

  const handlePhoneScan = async() => {
      const picked = await ImagePicker.launchCameraAsync({ quality: 0.7 })
      if (picked.canceled) return
      const asset = picked.assets[0]

      isLoading(true)
      try{
          const form = new FormData()
          form.append("image_file", {
              uri: asset.uri,
              name: asset.fileName ?? "scan.jpg",
              type: asset.mimeType ?? "image/jpeg",
          } as any)
          const res = await fetch(`${SERVER}/manualscan`, { method: "POST", body: form })
          if (!res.ok) throw new Error(`Scan failed: ${res.status}`)
          const data: ScanResult = await res.json()
          setResult(data) 
      }catch(e){
          console.error("Manual scan failed:", e)
      } finally {
          isLoading(false)
      }
  }


  const loadInventory = async () => {
      if (!SERVER) return;
      try {
          const res = await fetch(`${SERVER}/inventory`);
          if (!res.ok) return;
          const data = await res.json(); 
          if (data.items?.length) {
              setResult({ inventory: { items: data.items, reasoning: "" }, shopping: null });
              if (JSON.stringify(data.items) !== prevSigRef.current) {
                  setScanning(false)
              }
          }
      } catch (e) {
          console.error("Failed to load inventory:", e);
      }
  };

  useEffect(() => {
      loadInventory();                        
      const id = setInterval(loadInventory, 10000); 
      return () => clearInterval(id);           
  }, []);

  return (
    <ScrollView
      style={{ backgroundColor: "#00001B" }}
      contentContainerStyle={{ flexGrow: 1 }}
    >
    <SafeAreaView style={styles.container}>

      <Text style={styles.header1}>Hello Avneet!</Text>
      <Text style={styles.header}>View your recent reports</Text>
      <View style ={styles.report}>
        <Text style={styles.header}>Current Inventory</Text>
        {(loading || scanning) ? (
          <ActivityIndicator size="large" color="white" style={{ marginVertical: 20 }} />
        ) : (
          (result?.inventory?.items ?? fakeData).map((item, i) => (
            <ReportCard key={item.name ?? i} {...item} />
          ))
        )}
      </View>
      <View style ={styles.buttons}>
      <Pressable style = {styles.button} onPress={handleScan}>
          <Text style={styles.button}>New Scan</Text>
      </Pressable>
          <Pressable style = {styles.button} onPress={handlePhoneScan} disabled={loading}>
          <Text style={styles.button}>{loading ? "Scanning..." : "Phone Scan"}</Text>
      </Pressable>
      </View>
    </SafeAreaView>
     </ScrollView>

  )
}

const styles = StyleSheet.create({
  buttons:{
    gap:12,
    marginTop:20,
    alignItems:"center",
    justifyContent:"center",
    alignSelf:"center",
  },
  descText:{
    color:"white",
    marginTop:8,
  },
  metaRow:{
    flexDirection:"row",
    justifyContent:"flex-end",
    gap:8,
  },
  meta:{
    color:"#aaa",
    fontSize:12
  },
  rightSide:{
    flex:1,
    paddingLeft:12,
  },
  imageEl:{
    width:80,
    height:80,
    borderRadius:8,
  },
  container: {
    flex:1,
    backgroundColor:"#00001B",
    justifyContent:"flex-start",
    alignItems:"flex-start",
  },
  button:{
    color:'white',
    fontSize:15,
    justifyContent:"center",
    alignSelf:"center",
    backgroundColor:"orange",
    borderRadius:12,
    padding:5,
  },
  header1:{
    color:'white',
    fontWeight:"bold",
    fontSize:45,
    padding:10
  },
  header: {
    color:'white',
    fontWeight:"bold",
    fontSize:25,
    paddingLeft:20
  },
  report: {
    backgroundColor:"#00003B",
    flexDirection:"column",
    padding:20,
    borderRadius:12,
    width:"90%",
    alignSelf:"center"
  },
  card:{
    flexDirection:"row",
    borderColor:"white",
    width:"100%"
  }
});
