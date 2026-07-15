import { useFocusEffect } from '@react-navigation/native';
import Constants from 'expo-constants';
import { useRouter } from 'expo-router';
import * as WebBrowser from 'expo-web-browser';
import { Newspaper, Search, Star } from 'lucide-react-native';
import { useCallback, useMemo, useState } from 'react';
import { ActivityIndicator, FlatList, Pressable, StyleSheet } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { ThemedText } from '@/components/themed-text';
import { ThemedView } from '@/components/themed-view';
import { Button, ButtonText } from '@/components/ui/button';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Input, InputField, InputIcon, InputSlot } from '@/components/ui/input';
import { authHeaders, clearAuthToken, getAuthToken } from '@/lib/auth';

// Expo Go에서 실제 기기로 QR을 찍으면 'localhost'는 기기 자신을 가리키므로,
// 개발 서버(Metro)가 떠 있는 호스트(PC의 LAN IP)를 그대로 재사용한다.
function resolveApiHost() {
  const hostUri = Constants.expoConfig?.hostUri ?? Constants.expoGoConfig?.debuggerHost;
  const host = hostUri?.split(':')[0];
  return host || 'localhost';
}

const API_HOST = resolveApiHost();
const NEWS_API_URL = `http://${API_HOST}:8000/v1/news/`;
const FAVORITES_API_URL = `http://${API_HOST}:8000/v1/news/favorites/`;
const ME_API_URL = `http://${API_HOST}:8000/v1/users/me/`;
const SIGNOUT_API_URL = `http://${API_HOST}:8000/v1/users/signout/`;

type NewsItem = {
  id: string;
  title: string;
  pub_date: string;
  source: string;
  link: string;
  is_favorite: boolean;
};

export default function NewsScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const [items, setItems] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState('');
  const [showFavoritesOnly, setShowFavoritesOnly] = useState(false);
  const [username, setUsername] = useState<string | null>(null);

  const loadNews = useCallback(async () => {
    try {
      setError(null);
      const response = await fetch(NEWS_API_URL, { headers: await authHeaders() });
      const json = await response.json();
      setItems(json.data ?? []);
    } catch (e) {
      setError('뉴스를 불러오지 못했습니다.');
    } finally {
      setLoading(false);
    }
  }, []);

  const loadMe = useCallback(async () => {
    const token = await getAuthToken();
    if (!token) {
      setUsername(null);
      return;
    }
    try {
      const response = await fetch(ME_API_URL, { headers: await authHeaders() });
      const json = await response.json();
      setUsername(json.status === 'OK' ? json.user.username : null);
    } catch (e) {
      setUsername(null);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      loadNews();
      loadMe();
    }, [loadNews, loadMe])
  );

  const handleAccountPress = useCallback(async () => {
    if (!username) {
      router.push('/login');
      return;
    }
    await fetch(SIGNOUT_API_URL, { headers: await authHeaders() });
    await clearAuthToken();
    setUsername(null);
    loadNews();
  }, [username, router, loadNews]);

  const toggleFavorite = useCallback(
    async (item: NewsItem) => {
      if (!username) {
        router.push('/login');
        return;
      }

      const nextIsFavorite = !item.is_favorite;
      setItems((prev) =>
        prev.map((it) => (it.id === item.id ? { ...it, is_favorite: nextIsFavorite } : it))
      );

      try {
        const headers = await authHeaders();
        if (nextIsFavorite) {
          await fetch(FAVORITES_API_URL, {
            method: 'POST',
            headers: { ...headers, 'Content-Type': 'application/json' },
            body: JSON.stringify({ news_item_id: item.id }),
          });
        } else {
          await fetch(`${FAVORITES_API_URL}${item.id}/`, {
            method: 'DELETE',
            headers,
          });
        }
      } catch (e) {
        // 실패하면 낙관적으로 바꿨던 상태를 되돌린다.
        setItems((prev) =>
          prev.map((it) => (it.id === item.id ? { ...it, is_favorite: item.is_favorite } : it))
        );
      }
    },
    [username, router]
  );

  const visibleItems = useMemo(() => {
    const keyword = query.trim().toLowerCase();
    return items
      .filter((item) => !showFavoritesOnly || item.is_favorite)
      .filter(
        (item) =>
          !keyword ||
          item.title.toLowerCase().includes(keyword) ||
          item.source?.toLowerCase().includes(keyword)
      );
  }, [items, query, showFavoritesOnly]);

  return (
    <ThemedView style={styles.container}>
      <HStack
        space="xs"
        style={[styles.header, { height: 56 + insets.top, paddingTop: insets.top }]}
      >
        <Heading size="md" style={{ flex: 1, textAlign: 'center' }}>
          News
        </Heading>
        <Icon as={Newspaper} size="sm" />
        <Pressable onPress={handleAccountPress} style={{ position: 'absolute', right: 16, bottom: 12 }}>
          <ThemedText type="link">{username ?? '로그인'}</ThemedText>
        </Pressable>
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
            keyExtractor={(item, index) => item.id ?? String(index)}
            contentContainerStyle={styles.list}
            renderItem={({ item }) => (
              <Pressable onPress={() => WebBrowser.openBrowserAsync(item.link)}>
                <ThemedView style={styles.item}>
                  <HStack space="sm" style={{ alignItems: 'flex-start', justifyContent: 'space-between' }}>
                    <ThemedText type="defaultSemiBold" style={{ flex: 1 }}>
                      {item.title}
                    </ThemedText>
                    <Pressable hitSlop={8} onPress={() => toggleFavorite(item)}>
                      <Icon
                        as={Star}
                        fill={item.is_favorite ? '#f5c518' : 'none'}
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
