import { Image, Linking, Pressable, Text, View, StyleSheet } from "react-native";

interface shoppingItems {
    item: string,
    amount: number,
    price: number,
    link: string,
    image: string,
}

export default function ShopList({ item, amount, price, link, image }: shoppingItems) {
    return (
        <View style={styles.card}>
            <Image source={{ uri: image }} style={styles.image} />

            <View style={styles.meta}>
                <Text style={styles.metaText}>Amount: {amount}</Text>
                <Text style={styles.metaText}>${price.toFixed(2)}</Text>
            </View>

            <Text style={styles.title}>{item}</Text>

            {link ? (
                <Pressable onPress={() => Linking.openURL(link)}>
                    <Text style={styles.link}>Buy</Text>
                </Pressable>
            ) : null}
        </View>
    );
}

const styles = StyleSheet.create({
    card: {
        flexDirection: "column",
        backgroundColor: "#00003B",
        borderRadius: 12,
        padding: 12,
        marginVertical: 6,
        width: "48%",   // two cards per row (parent wraps + space-between)
    },
    image: {
        width: "100%",
        height: 150,
        borderRadius: 8,
        backgroundColor: "#11224a", 
    },
    meta: {
        flexDirection: "row",
        justifyContent: "space-between",
        marginTop: 8,
    },
    metaText: {
        color: "#aaa",
        fontSize: 12,
    },
    title: {
        color: "white",
        fontSize: 16,
        fontWeight: "bold",
        marginTop: 6,
    },
    link: {
        color: "white",
        borderColor: "orange",
        borderWidth: 1,
        borderRadius: 8,
        paddingVertical: 4,
        paddingHorizontal: 14,
        marginTop: 8,
        fontWeight: "600",
        alignSelf: "flex-start",
        overflow: "hidden",
    },
});
