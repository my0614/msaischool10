import { useEffect, useMemo, useState } from 'react';
import { FlatList } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Home } from 'lucide-react-native';

import UserItem from '@/components/ui/user-item';
import { Box } from '@/components/ui/box';
import { Button, ButtonText } from '@/components/ui/button';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

const PEOPLE = [
  { name: '정종현', description: '오늘은 수요일입니다.' },
  { name: '김철수', description: '오늘은 목요일입니다.' },
  { name: '이영희', description: '오늘은 금요일입니다.' },
];

export default function HomeScreen() {
  const insets = useSafeAreaInsets();
  const [name, setName] = useState('정종현');
  const [isInitialized, setIsInitialized] = useState(false);
  const [data, setData] = useState({ address: '서울시 강남구' });

  const people = useMemo(
    () =>
      PEOPLE.map((person) => ({
        ...person,
        imageUrl: `https://i.pravatar.cc/150?img=${Math.floor(Math.random() * 70) + 1}`,
      })),
    []
  );

  useEffect(() => {
    console.log('HOME SCREEN RENDERED', isInitialized);
  }, []);

  useEffect(() => {
    if (isInitialized) {
      console.log('2. 주소 변경', data.address);
      setData({ address: '부산시 해운대구' });
    }
    setIsInitialized(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [name]);

  useEffect(() => {
    console.log('3. 주소 변경 완료', data.address);
  }, [data]);

  return (
    <Box style={{ flex: 1 }}>
      <HStack
        space="xs"
        style={{
          height: 56 + insets.top,
          paddingTop: insets.top,
          alignItems: 'center',
          justifyContent: 'center',
          borderBottomWidth: 1,
          borderBottomColor: '#222',
        }}
      >
        <Heading size="md">Home</Heading>
        <Icon as={Home} size="sm" />
      </HStack>

      <VStack style={{ marginVertical: 20, marginHorizontal: 20 }}>
        <Text>{name}</Text>
        <Text>{data.address}</Text>
        <Button
          onPress={() => {
            setName('김철수');
            console.log('1. 이름 변경', name);
          }}
        >
          <ButtonText>이름 변경</ButtonText>
        </Button>
      </VStack>

      <VStack space="2xl">
        <FlatList
          data={people}
          contentContainerStyle={{ padding: 16, gap: 12 }}
          renderItem={({ item }) => (
            <UserItem name={item.name} description={item.description} imageUrl={item.imageUrl} />
          )}
          keyExtractor={(item) => item.name}
        />
      </VStack>
    </Box>
  );
}
