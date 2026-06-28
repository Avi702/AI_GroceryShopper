import React from 'react'
import { ActivityIndicator, Alert, Image, Pressable, Text, View, StyleSheet, ScrollView } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import {router} from "expo-router"
export default function Shop(){
    return (<SafeAreaView style = {styles.container}>
        <Text style={styles.header}>Recommended Items</Text>
        <Text style = {styles.subheader}>Powered by AI</Text>
        <ScrollView>
            <View style = {styles.card}>
                <Image></Image>
                    <View>
                        <View></View>
                        <Text></Text>
                    </View>
            </View>
        </ScrollView>
    </SafeAreaView>);
}

const styles = StyleSheet.create({
    container: {
        flex:1,
        backgroundColor:"#00001B",
        justifyContent:"flex-start",
        alignItems:"flex-start",
    },
    header:{
    color:'white',
    fontWeight:"bold",
    fontSize:35,
    padding:10,
    },
    subheader:{
    color:'orange',
    fontWeight:"bold",
    fontSize:20,
    padding:10,
    },
    card:{
        backgroundColor:"white",
        borderColor:"white",
        height:50,
        width:"100%",
    },
})