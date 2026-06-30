import React from 'react'
import { ActivityIndicator, Alert, Image, Pressable, Text, View, StyleSheet, ScrollView } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import ShopList from "../components/ShopList";
import { router, useFocusEffect } from "expo-router";
import { useState, useCallback } from "react";
const fakeData = {
    item: "apples", amount: 2, price: 3.50, link: "https://www.google.com", image: "", 
}

type ShopItem = { name: string; amount: number; price: number; link: string; store: string; image_url: string };

export default function Shop(){
    const [shopping, setShopping] = useState<ShopItem[]>([]);
    const SERVER = process.env.EXPO_PUBLIC_SERVER_URL
    useFocusEffect(useCallback(()=>{
        fetch(`${SERVER}/shopping`)
        .then(r => r.json())
        .then(d => setShopping(d["shopping-list"] ?? []))
        .catch(console.error)
    },[SERVER]))
    return (<SafeAreaView style = {styles.container}>
        <Text style={styles.header}>Recommended Items</Text>
        <Text style = {styles.subheader}>Powered by AI</Text>
        <ScrollView style={{ width: "100%" }} contentContainerStyle={styles.grid}>
            {shopping.map ((s, i) => (
                <ShopList 
                key ={i}
                item = {s.name}
                amount = {s.amount}
                price = {s.price}
                link = {s.link}
                image = {s.image_url}/>))}
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
    grid:{
        flexDirection:"row",
        flexWrap:"wrap",
        justifyContent:"space-between",
        paddingHorizontal:10,
    },
    card:{
        backgroundColor:"white",
        borderColor:"white",
        height:50,
        width:"100%",
    },
})