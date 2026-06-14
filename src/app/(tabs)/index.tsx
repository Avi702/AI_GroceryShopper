import { Image, Pressable, Text, View, StyleSheet } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import {router} from "expo-router"
interface groceryItems{
  time: string,
  date: string,
  image: string,
  description: string,
  items: number
}
export default function Index({time,date,image,description,items}:groceryItems) {
  return (
    <SafeAreaView style={styles.container}>
      <Text style={styles.header1}>Hello Avneet!</Text>
      <Text style={styles.header}>View your recent reports</Text>
      <View style ={styles.report}>
        <Text style={styles.header}>Add to your grocery list</Text>
        <View style ={styles.card}>
          <Image source = {{uri: image}} style = {styles.imageEl}></Image>
          <View style={styles.rightSide}>
            <View style={styles.metaRow}>
              <Text style = {styles.meta}>{date}</Text>
              <Text style = {styles.meta}>{time}</Text>
              <Text style = {styles.meta}>{items}</Text>
            </View>
            <Text style={styles.descText}>{description}</Text>
          </View>
        </View>
      </View>
      <View style ={styles.buttons}>
      <Pressable style = {styles.button} onPress={()=>console.log("tapped")}>
          <Text style={styles.button}>New Scan</Text>
        </Pressable>
      <Pressable style = {styles.button} onPress={()=>router.push("/Shop")}>
          <Text style={styles.button}>Purchase Items</Text>
      </Pressable>
      </View>
    </SafeAreaView>
  );
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
