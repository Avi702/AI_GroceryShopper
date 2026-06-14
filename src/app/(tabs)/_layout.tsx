import {Image,ImageBackground, StyleSheet, View, Text} from 'react-native'
import React from 'react'
import {Tabs} from "expo-router"
import {FontAwesome} from '@expo/vector-icons'
export default function _Layout(){
    return (
        <Tabs
            screenOptions ={{
                headerShown: false,
                tabBarActiveTintColor: 'blue',
                tabBarInactiveTintColor:"white",
                tabBarStyle: {
                    backgroundColor: '#00010B'
                }
            }}>
            <Tabs.Screen 
                name = "index"
                options ={{
                    title: "Home",
                    headerShown: false,
                    tabBarIcon: ({color,size})=>(
                        <FontAwesome name ="home" size={size} color={color}/>
                    )
                }}
            />
            <Tabs.Screen 
                name = "Shop"
                options ={{
                    title: "Shop",
                    headerShown: false,
                    tabBarIcon: ({color,size})=>(
                        <FontAwesome name ="shopping-cart" size={size} color={color}/>
                    )}}
            />
            <Tabs.Screen 
                name = "Profile"
                options ={{
                    title: "Profile",
                    headerShown: false,
                    tabBarIcon: ({color,size})=>(
                        <FontAwesome name ="user" size={size} color={color}/>
                    )}}
            />
        </Tabs>
        )
}

const styles = StyleSheet.create({
    container:{
        flex: 1,
        alignItems:"flex-end",
        justifyContent:"flex-end"
    }
})