import { useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  Animated,
  FlatList,
  Image,
  Pressable,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { StatusBar } from "expo-status-bar";
import axios from "axios";

// 위키백과 요약 API에는 없는 정보라 고정값으로 둔다
const PHILOSOPHERS = [
  { name: "소크라테스", wikiTitle: "소크라테스", nickname: "아테네의 등에" },
  { name: "플라톤", wikiTitle: "플라톤", nickname: "어깨 넓은 아리스토클레스" },
  { name: "아리스토텔레스", wikiTitle: "아리스토텔레스", nickname: "스타게이라의 현자" },
  { name: "칸트", wikiTitle: "임마누엘_칸트", nickname: "쾨니히스베르크의 시계" },
  { name: "니체", wikiTitle: "프리드리히_니체", nickname: "망치를 든 철학자" },
];

function truncate(text, max) {
  if (!text || text.length <= max) return text;
  return `${text.slice(0, max)}...`;
}

async function fetchPhilosophers() {
  const [results] = await Promise.all([
    Promise.all(
      PHILOSOPHERS.map(async (p) => {
        const { data } = await axios.get(
          `https://ko.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(p.wikiTitle)}`
        );
        return {
          name: p.name,
          nickname: p.nickname,
          intro: truncate(data.extract, 70),
          img: data.thumbnail?.source,
        };
      })
    ),
    new Promise((resolve) => setTimeout(resolve, 2000)),
  ]);
  return results;
}

function MemberCard({ name, intro, nickname, img }) {
  const anim = useRef(new Animated.Value(0)).current;
  const [flipped, setFlipped] = useState(false);

  const toggleFlip = () => {
    Animated.timing(anim, {
      toValue: flipped ? 0 : 180,
      duration: 500,
      useNativeDriver: true,
    }).start();
    setFlipped((prev) => !prev);
  };

  const frontRotate = anim.interpolate({
    inputRange: [0, 180],
    outputRange: ["0deg", "180deg"],
  });
  const backRotate = anim.interpolate({
    inputRange: [0, 180],
    outputRange: ["180deg", "360deg"],
  });

  return (
    <Pressable onPress={toggleFlip} style={styles.card}>
      <Animated.View
        style={[
          styles.cardFace,
          { transform: [{ rotateY: frontRotate }] },
        ]}
      >
        <View style={styles.cardImgWrap}>
          {img ? (
            <Image source={{ uri: img }} style={styles.cardImg} />
          ) : (
            <View style={[styles.cardImg, styles.cardImgFallback]} />
          )}
        </View>
        <View style={styles.cardBody}>
          <Text style={styles.cardName}>{name}</Text>
          <Text style={styles.cardIntro} numberOfLines={3}>
            {intro}
          </Text>
        </View>
      </Animated.View>

      <Animated.View
        style={[
          styles.cardFace,
          styles.cardBack,
          { transform: [{ rotateY: backRotate }] },
        ]}
      >
        <Text style={styles.cardBackLabel}>별명</Text>
        <Text style={styles.cardBackNickname}>{nickname}</Text>
        <Text style={styles.cardBackName}>{name}</Text>
      </Animated.View>
    </Pressable>
  );
}

export default function App() {
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    fetchPhilosophers()
      .then((data) => {
        if (cancelled) return;
        setMembers(data);
      })
      .catch(() => {
        if (!cancelled) setError("철학자 정보를 불러오지 못했어요.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [retryCount]);

  return (
    <View style={styles.wrap}>
      <StatusBar style="light" />
      <Text style={styles.title}>철학소년단</Text>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color="#e9e4f7" />
          <Text style={styles.loadingText}>철학자들을 불러오는 중...</Text>
        </View>
      ) : error ? (
        <View style={styles.center}>
          <Text style={styles.errorText}>{error}</Text>
          <Pressable style={styles.retryBtn} onPress={() => setRetryCount((c) => c + 1)}>
            <Text style={styles.retryBtnText}>다시 시도</Text>
          </Pressable>
        </View>
      ) : (
        <FlatList
          data={members}
          keyExtractor={(item) => item.name}
          numColumns={2}
          columnWrapperStyle={styles.row}
          contentContainerStyle={styles.list}
          renderItem={({ item }) => <MemberCard {...item} />}
        />
      )}
    </View>
  );
}

const CARD_HEIGHT = 260;

const styles = StyleSheet.create({
  wrap: {
    flex: 1,
    backgroundColor: "#4b3f6b",
    paddingTop: 64,
  },
  title: {
    textAlign: "center",
    color: "#ffffff",
    fontWeight: "900",
    letterSpacing: 4,
    fontSize: 32,
    marginBottom: 24,
  },
  center: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    gap: 16,
  },
  loadingText: {
    color: "#e9e4f7",
    fontSize: 16,
  },
  errorText: {
    color: "#fca5a5",
    fontSize: 16,
    marginBottom: 12,
  },
  retryBtn: {
    borderWidth: 1,
    borderColor: "rgba(233,228,247,0.4)",
    backgroundColor: "rgba(255,255,255,0.08)",
    paddingVertical: 8,
    paddingHorizontal: 24,
    borderRadius: 999,
  },
  retryBtnText: {
    color: "#e9e4f7",
    fontSize: 14,
  },
  list: {
    paddingHorizontal: 12,
    paddingBottom: 24,
  },
  row: {
    gap: 12,
  },
  card: {
    flex: 1,
    height: CARD_HEIGHT,
    marginBottom: 12,
    borderRadius: 16,
    overflow: "hidden",
    backgroundColor: "#ffffff",
  },
  cardFace: {
    position: "absolute",
    width: "100%",
    height: "100%",
    backfaceVisibility: "hidden",
    borderRadius: 16,
    overflow: "hidden",
    backgroundColor: "#ffffff",
  },
  cardBack: {
    backgroundColor: "#2c2440",
    alignItems: "center",
    justifyContent: "center",
    padding: 16,
    gap: 6,
  },
  cardImgWrap: {
    width: "100%",
    height: "60%",
    backgroundColor: "#e5e5e5",
  },
  cardImg: {
    width: "100%",
    height: "100%",
    resizeMode: "cover",
  },
  cardImgFallback: {
    backgroundColor: "#d4d4d8",
  },
  cardBody: {
    padding: 10,
  },
  cardName: {
    fontSize: 15,
    fontWeight: "700",
    color: "#3f3f46",
    marginBottom: 4,
  },
  cardIntro: {
    fontSize: 11,
    color: "#a1a1aa",
    lineHeight: 15,
  },
  cardBackLabel: {
    fontSize: 11,
    letterSpacing: 2,
    color: "#c4b5fd",
  },
  cardBackNickname: {
    fontSize: 15,
    fontWeight: "700",
    color: "#ffffff",
    textAlign: "center",
  },
  cardBackName: {
    fontSize: 12,
    color: "#a1a1aa",
  },
});
