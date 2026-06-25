import { Image, Pressable, Text, View, StyleSheet } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import {router} from "expo-router"
import ReportCard from "../components/ReportCard";
import {useState} from "react"
const fakeData = {
  time: "10:30AM",
  date: "10/17/2025",
  image:"https://images.unsplash.com/photo-1550583724-b2692b85b150",
  description: "2% milk",
  items: 3
}

export default function Index() {
  const [loading, isLoading] = useState(false)
  const [result, setResult] = useState(null)
  const SERVER = process.env.EXPO_PUBLIC_SERVER_URL;
  const handleScan = async() => {
      isLoading(true)
      try{
          await fetch(`${SERVER}/request-scan`, { method: "POST" });
      }catch(e){
          console.error("Scan request failed:", e);
      } finally {
          isLoading(false);
      }
  }
  return (
    <SafeAreaView style={styles.container}>
      <Text style={styles.header1}>Hello Avneet!</Text>
      <Text style={styles.header}>View your recent reports</Text>
      <View style ={styles.report}>
        <Text style={styles.header}>Current Inventory</Text>
        <ReportCard {...fakeData}/>
      </View>
      <View style ={styles.buttons}>
      <Pressable style = {styles.button} onPress={()=>console.log("tapped")}>
          <Text style={styles.button}>New Scan</Text>
      </Pressable>
          <Pressable style = {styles.button} onPress={()=>router.push("/Shop")}>
          <Text style={styles.button}>Phone Scan</Text>
      </Pressable>
      <Pressable style = {styles.button} onPress={()=>router.push("/Shop")}>
          <Text style={styles.button}>Purchase Items</Text>
      </Pressable>
      </View>
    </SafeAreaView>
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
