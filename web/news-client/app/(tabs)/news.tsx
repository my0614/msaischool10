import AsyncStorage from '@react-native-async-storage/async-storage';
import Constants from 'expo-constants';
import * as WebBrowser from 'expo-web-browser';
import { Newspaper, Search, Star } from 'lucide-react-native';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, FlatList, Pressable, StyleSheet } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { ThemedText } from '@/components/themed-text';
import { ThemedView } from '@/components/themed-view';
import { Button, ButtonText } from '@/components/ui/button';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Input, InputField, InputIcon, InputSlot } from '@/components/ui/input';

// Expo Go에서 실제 기기로 QR을 찍으면 'localhost'는 기기 자신을 가리키므로,
// 개발 서버(Metro)가 떠 있는 호스트(PC의 LAN IP)를 그대로 재사용한다.
function resolveApiHost() {
  const hostUri = Constants.expoConfig?.hostUri ?? Constants.expoGoConfig?.debuggerHost;
  const host = hostUri?.split(':')[0];
  return host || 'localhost';
}

const NEWS_API_URL = `http://${resolveApiHost()}:8000/v1/news/`;
const FAVORITES_STORAGE_KEY = 'news:favorites';

type NewsItem = {
  title: string;
  pub_date: string;
  source: string;
  link: string;
};

export default function NewsScreen() {
  const insets = useSafeAreaInsets();
  const [items, setItems] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState('');
  const [favorites, setFavorites] = useState<Set<string>>(new Set());
  const [showFavoritesOnly, setShowFavoritesOnly] = useState(false);

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

  useEffect(() => {
    AsyncStorage.getItem(FAVORITES_STORAGE_KEY).then((stored) => {
      if (stored) {
        setFavorites(new Set(JSON.parse(stored)));
      }
    });
  }, []);

  const toggleFavorite = useCallback((link: string) => {
    setFavorites((prev) => {
      const next = new Set(prev);
      if (next.has(link)) {
        next.delete(link);
      } else {
        next.add(link);
      }
      AsyncStorage.setItem(FAVORITES_STORAGE_KEY, JSON.stringify([...next]));
      return next;
    });
  }, []);

  const visibleItems = useMemo(() => {
    const keyword = query.trim().toLowerCase();
    return items
      .filter((item) => !showFavoritesOnly || favorites.has(item.link))
      .filter(
        (item) =>
          !keyword ||
          item.title.toLowerCase().includes(keyword) ||
          item.source?.toLowerCase().includes(keyword)
      );
  }, [items, query, showFavoritesOnly, favorites]);

  return (
    <ThemedView style={styles.container}>
      <HStack
        space="xs"
        style={[styles.header, { height: 56 + insets.top, paddingTop: insets.top }]}
      >
        <Heading size="md">News</Heading>
        <Icon as={Newspaper} size="sm" />
      </HStack>

      {loading ? (
        <ThemedView style={styles.centered}>
          <ActivityIndicator />
        </ThemedView>
      ) : error ? (
        <ThemedView style={styles.centered}>
          <ThemedText>{error}</ThemedText>
        </ThemedView>
      ) : (
        <>
          <HStack space="sm" style={styles.toolbar}>
            <Input style={styles.searchInput}>
              <InputSlot style={{ paddingLeft: 8 }}>
                <InputIcon as={Search} />
              </InputSlot>
              <InputField
                placeholder="제목/언론사 검색"
                value={query}
                onChangeText={setQuery}
              />
            </Input>
            <Button
              variant={showFavoritesOnly ? 'default' : 'outline'}
              onPress={() => setShowFavoritesOnly((prev) => !prev)}
            >
              <ButtonText>즐겨찾기</ButtonText>
            </Button>
          </HStack>

          <FlatList
            data={visibleItems}
            keyExtractor={(item, index) => item.link ?? String(index)}
            contentContainerStyle={styles.list}
            renderItem={({ item }) => (
              <Pressable onPress={() => WebBrowser.openBrowserAsync(item.link)}>
                <ThemedView style={styles.item}>
                  <HStack space="sm" style={{ alignItems: 'flex-start', justifyContent: 'space-between' }}>
                    <ThemedText type="defaultSemiBold" style={{ flex: 1 }}>
                      {item.title}
                    </ThemedText>
                    <Pressable hitSlop={8} onPress={() => toggleFavorite(item.link)}>
                      <Icon
                        as={Star}
                        fill={favorites.has(item.link) ? '#f5c518' : 'none'}
                        color="#f5c518"
                      />
                    </Pressable>
                  </HStack>
                  <ThemedText>
                    {item.source} · {item.pub_date}
                  </ThemedText>
                </ThemedView>
              </Pressable>
            )}
          />
        </>
      )}
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
  header: {
    alignItems: 'center',
    justifyContent: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#222',
  },
  toolbar: {
    paddingHorizontal: 16,
    paddingTop: 16,
    alignItems: 'center',
  },
  searchInput: {
    flex: 1,
  },
  list: {
    padding: 16,
    gap: 12,
  },
  item: {
    gap: 4,
  },
});
