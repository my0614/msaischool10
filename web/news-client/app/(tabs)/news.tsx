import Constants from 'expo-constants';
import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, FlatList, StyleSheet } from 'react-native';

import { ThemedText } from '@/components/themed-text';
import { ThemedView } from '@/components/themed-view';

// Expo Go에서 실제 기기로 QR을 찍으면 'localhost'는 기기 자신을 가리키므로,
// 개발 서버(Metro)가 떠 있는 호스트(PC의 LAN IP)를 그대로 재사용한다.
function resolveApiHost() {
  const hostUri = Constants.expoConfig?.hostUri ?? Constants.expoGoConfig?.debuggerHost;
  const host = hostUri?.split(':')[0];
  return host || 'localhost';
}

const NEWS_API_URL = `http://${resolveApiHost()}:8000/v1/news/`;

type NewsItem = {
  title: string;
  pub_date: string;
  source: string;
  link: string;
};

export default function NewsScreen() {
  const [items, setItems] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadNews = useCallback(async () => {
    try {
      setError(null);
      const response = await fetch(NEWS_API_URL);
      const json = await response.json();
      setItems(json.data ?? []);
    } catch (e) {
      setError('뉴스를 불러오지 못했습니다.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadNews();
  }, [loadNews]);

  if (loading) {
    return (
      <ThemedView style={styles.centered}>
        <ActivityIndicator />
      </ThemedView>
    );
  }

  if (error) {
    return (
      <ThemedView style={styles.centered}>
        <ThemedText>{error}</ThemedText>
      </ThemedView>
    );
  }

  return (
    <ThemedView style={styles.container}>
      <FlatList
        data={items}
        keyExtractor={(item, index) => item.link ?? String(index)}
        contentContainerStyle={styles.list}
        renderItem={({ item }) => (
          <ThemedView style={styles.item}>
            <ThemedText type="defaultSemiBold">{item.title}</ThemedText>
            <ThemedText>
              {item.source} · {item.pub_date}
            </ThemedText>
          </ThemedView>
        )}
      />
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  centered: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  list: {
    padding: 16,
    gap: 12,
  },
  item: {
    gap: 4,
  },
});
