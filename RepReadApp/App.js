import React from 'react';
import { View, Text } from 'react-native';

export default function App() {
  return (
    <View style={{
      flex: 1,
      backgroundColor: '#000000',
      justifyContent: 'center',
      alignItems: 'center'
    }}>
      <Text style={{
        color: '#ffffff',
        fontSize: 24,
        fontWeight: 'bold'
      }}>
        RepRead Works!
      </Text>
      <Text style={{
        color: '#cccccc',
        fontSize: 16,
        marginTop: 10
      }}>
        If you see this, React Native is working
      </Text>
    </View>
  );
}
