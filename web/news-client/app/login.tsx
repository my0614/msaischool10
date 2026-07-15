import Constants from 'expo-constants';
import { useRouter } from 'expo-router';
import { useState } from 'react';
import { ActivityIndicator } from 'react-native';

import { ThemedView } from '@/components/themed-view';
import { Button, ButtonText } from '@/components/ui/button';
import { Heading } from '@/components/ui/heading';
import { Input, InputField } from '@/components/ui/input';
import { Text } from '@/components/ui/text';
import { VStack } from '@/components/ui/vstack';

function resolveApiHost() {
  const hostUri = Constants.expoConfig?.hostUri ?? Constants.expoGoConfig?.debuggerHost;
  const host = hostUri?.split(':')[0];
  return host || 'localhost';
}

const USER_API_BASE = `http://${resolveApiHost()}:8000/v1/users`;

export default function LoginScreen() {
  const router = useRouter();
  const [mode, setMode] = useState<'signin' | 'signup'>('signin');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${USER_API_BASE}/${mode}/`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      const json = await response.json();
      if (json.status !== 'OK') {
        setError(json.message ?? '요청에 실패했습니다.');
        return;
      }
      router.back();
    } catch (e) {
      setError('서버에 연결할 수 없습니다.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ThemedView style={{ flex: 1, justifyContent: 'center', padding: 24 }}>
      <VStack space="md">
        <Heading size="lg">{mode === 'signin' ? '로그인' : '회원가입'}</Heading>
        <Input>
          <InputField
            placeholder="이메일"
            autoCapitalize="none"
            keyboardType="email-address"
            value={username}
            onChangeText={setUsername}
          />
        </Input>
        <Input>
          <InputField
            placeholder="비밀번호"
            secureTextEntry
            value={password}
            onChangeText={setPassword}
          />
        </Input>
        {error && <Text style={{ color: '#e11d48' }}>{error}</Text>}
        <Button onPress={submit} disabled={loading}>
          {loading ? (
            <ActivityIndicator />
          ) : (
            <ButtonText>{mode === 'signin' ? '로그인' : '가입하기'}</ButtonText>
          )}
        </Button>
        <Button
          variant="link"
          onPress={() => setMode((prev) => (prev === 'signin' ? 'signup' : 'signin'))}
        >
          <ButtonText>
            {mode === 'signin' ? '계정이 없나요? 회원가입' : '이미 계정이 있나요? 로그인'}
          </ButtonText>
        </Button>
      </VStack>
    </ThemedView>
  );
}
