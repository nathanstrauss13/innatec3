import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { StatusBar } from 'react-native';

import InputScreen from '../screens/InputScreen';
import LoadingScreen from '../screens/LoadingScreen';
import ResultsScreen from '../screens/ResultsScreen';

import { colors } from '../styles/styles';

const Stack = createStackNavigator();

const AppNavigator = () => {
  return (
    <NavigationContainer>
      <StatusBar 
        barStyle="light-content" 
        backgroundColor={colors.gray900}
        translucent={false}
      />
      <Stack.Navigator
        initialRouteName="Input"
        screenOptions={{
          headerStyle: {
            backgroundColor: colors.gray900,
            borderBottomWidth: 1,
            borderBottomColor: colors.gray700,
          },
          headerTintColor: colors.white,
          headerTitleStyle: {
            fontWeight: '600',
            fontSize: 18,
          },
          headerBackTitleVisible: false,
          gestureEnabled: true,
          cardStyle: { backgroundColor: colors.gray900 },
        }}
      >
        <Stack.Screen 
          name="Input" 
          component={InputScreen}
          options={{
            title: 'RepEnhance',
            headerShown: false, // Hide header for input screen
          }}
        />
        <Stack.Screen 
          name="Loading" 
          component={LoadingScreen}
          options={{
            title: 'Analyzing...',
            headerShown: false, // Hide header for loading screen
            gestureEnabled: false, // Prevent going back during loading
          }}
        />
        <Stack.Screen 
          name="Results" 
          component={ResultsScreen}
          options={{
            title: 'AI Reputation Report',
            headerShown: false,
          }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
};

export default AppNavigator;
