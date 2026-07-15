import { Avatar, AvatarBadge, AvatarFallbackText, AvatarImage } from '@/components/ui/avatar';
import { Heading } from '@/components/ui/heading';
import { HStack } from '@/components/ui/hstack';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

interface UserItemProps {
  name?: string;
  description?: string;
  imageUrl?: string;
}

export default function UserItem({
  name,
  description,
  imageUrl,
}: UserItemProps) {
  return (
    <HStack space="md">
      <Avatar className="bg-indigo-600">
        <AvatarFallbackText className="text-white">{name}</AvatarFallbackText>
        {imageUrl && <AvatarImage source={{ uri: imageUrl }} />}
        <AvatarBadge />
      </Avatar>
      <VStack>
        <Heading size="sm">{name}</Heading>
        <Text size="sm">{description}</Text>
      </VStack>
    </HStack>
  );
}