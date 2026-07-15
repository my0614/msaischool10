import { ThemedView } from '@/components/themed-view';
import { Avatar, AvatarBadge, AvatarFallbackText, AvatarImage } from '@/components/ui/avatar';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Icon } from '@/components/ui/icon';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';
import { Home } from 'lucide-react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

type Person = {
  name: string;
  role: string;
  avatarUri?: string;
  avatarBg: string;
  online?: boolean;
};

const people: Person[] = [
  {
    name: 'Ronald Richards',
    role: 'Nursing Assistant',
    avatarUri:
      'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxzZWFyY2h8Mnx8dXNlcnxlbnwwfHwwfHw%3D&auto=format&fit=crop&w=800&q=60',
    avatarBg: 'bg-indigo-600',
    online: true,
  },
  {
    name: 'Arlene McCoy',
    role: 'Marketing Coordinator',
    avatarBg: 'bg-orange-600',
  },
];

export default function HomeScreen() {
  const insets = useSafeAreaInsets();

  return (
    <ThemedView style={{ flex: 1 }}>
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

      <VStack space="2xl" style={{ padding: 16, paddingTop: 24 }}>
        {people.map((person) => (
          <HStack key={person.name} space="md" style={{ alignItems: 'center' }}>
            <Avatar className={person.avatarBg}>
              <AvatarFallbackText className="text-white">{person.name}</AvatarFallbackText>
              {person.avatarUri && <AvatarImage source={{ uri: person.avatarUri }} />}
              {person.online && <AvatarBadge />}
            </Avatar>
            <VStack>
              <Heading size="sm">{person.name}</Heading>
              <Text size="sm">{person.role}</Text>
            </VStack>
          </HStack>
        ))}
      </VStack>
    </ThemedView>
  );
}