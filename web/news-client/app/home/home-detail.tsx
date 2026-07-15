import { ChevronLeft } from 'lucide-react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { Box } from '@/components/ui/box';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Pressable } from '@/components/ui/pressable';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

export default function HomeDetailScreen() {
  const insets = useSafeAreaInsets();
  const router = useRouter();

  return (
    <Box style={{ flex: 1 }}>
      <HStack
        space="sm"
        style={{
          height: 56 + insets.top,
          paddingTop: insets.top,
          paddingHorizontal: 16,
          alignItems: 'center',
          borderBottomWidth: 1,
          borderBottomColor: '#222',
        }}
      >
        <Pressable onPress={() => router.back()}>
          <Icon as={ChevronLeft} size="md" />
        </Pressable>
        <Heading size="md">홈 상세</Heading>
      </HStack>

      <VStack style={{ marginVertical: 20, marginHorizontal: 20 }}>
        <Text>Home Detail Screen</Text>
      </VStack>
    </Box>
  );
}
