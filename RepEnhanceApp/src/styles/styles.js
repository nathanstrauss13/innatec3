import { StyleSheet, Dimensions } from 'react-native';

const { width, height } = Dimensions.get('window');

export const colors = {
  // Gray scale (matching Tailwind)
  gray900: '#111827',
  gray800: '#1f2937',
  gray750: '#334155',
  gray700: '#374151',
  gray600: '#4b5563',
  gray500: '#6b7280',
  gray400: '#9ca3af',
  gray300: '#d1d5db',
  gray200: '#e5e7eb',
  gray100: '#f3f4f6',
  
  // Blue scale
  blue900: '#1e3a8a',
  blue700: '#1d4ed8',
  blue600: '#2563eb',
  blue500: '#3b82f6',
  blue400: '#60a5fa',
  blue300: '#93c5fd',
  
  // Purple scale
  purple600: '#9333ea',
  purple700: '#7c3aed',
  
  // Green scale
  green900: '#14532d',
  green700: '#15803d',
  green500: '#22c55e',
  green400: '#4ade80',
  green300: '#86efac',
  
  // Yellow scale
  yellow900: '#713f12',
  yellow700: '#a16207',
  yellow400: '#facc15',
  yellow300: '#fde047',
  yellow200: '#fef08a',
  
  // Red scale
  red900: '#7f1d1d',
  red700: '#b91c1c',
  red400: '#f87171',
  red300: '#fca5a5',
  
  // White and black
  white: '#ffffff',
  black: '#000000',
  transparent: 'transparent',
};

export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
  xxxl: 64,
};

export const borderRadius = {
  sm: 4,
  md: 8,
  lg: 12,
  xl: 16,
  xxl: 24,
  full: 9999,
};

export const fontSize = {
  xs: 12,
  sm: 14,
  base: 16,
  lg: 18,
  xl: 20,
  xxl: 24,
  xxxl: 30,
  xxxxl: 36,
};

export const fontWeight = {
  normal: '400',
  medium: '500',
  semibold: '600',
  bold: '700',
};

export const styles = StyleSheet.create({
  // Container styles
  container: {
    flex: 1,
    backgroundColor: colors.gray900,
  },
  
  safeArea: {
    flex: 1,
    backgroundColor: colors.gray900,
  },
  
  scrollContainer: {
    flexGrow: 1,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.lg,
  },
  
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: spacing.md,
  },
  
  // Card styles
  card: {
    backgroundColor: colors.gray800,
    borderRadius: borderRadius.xl,
    borderWidth: 1,
    borderColor: colors.gray700,
    padding: spacing.xl,
    marginBottom: spacing.lg,
  },
  
  cardHeader: {
    alignItems: 'center',
    marginBottom: spacing.xl,
  },
  
  // Text styles
  title: {
    fontSize: fontSize.xxxl,
    fontWeight: fontWeight.bold,
    color: colors.white,
    textAlign: 'center',
  },
  
  subtitle: {
    fontSize: fontSize.xl,
    fontWeight: fontWeight.medium,
    color: colors.gray300,
    textAlign: 'center',
    marginBottom: spacing.sm,
  },
  
  description: {
    fontSize: fontSize.base,
    color: colors.gray400,
    textAlign: 'center',
    lineHeight: 24,
  },
  
  sectionTitle: {
    fontSize: fontSize.xl,
    fontWeight: fontWeight.bold,
    color: colors.white,
    marginBottom: spacing.md,
  },
  
  label: {
    fontSize: fontSize.sm,
    fontWeight: fontWeight.medium,
    color: colors.gray200,
    marginBottom: spacing.sm,
  },
  
  errorText: {
    fontSize: fontSize.sm,
    color: colors.red300,
    textAlign: 'center',
  },
  
  // Input styles
  input: {
    backgroundColor: colors.gray700,
    borderWidth: 1,
    borderColor: colors.gray600,
    borderRadius: borderRadius.lg,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.md,
    fontSize: fontSize.base,
    color: colors.white,
    marginBottom: spacing.md,
  },
  
  inputFocused: {
    borderColor: colors.blue500,
    borderWidth: 2,
  },
  
  // Button styles
  primaryButton: {
    backgroundColor: colors.blue600,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    borderRadius: borderRadius.lg,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  
  primaryButtonPressed: {
    backgroundColor: colors.blue700,
  },
  
  primaryButtonDisabled: {
    backgroundColor: colors.gray600,
    opacity: 0.5,
  },
  
  buttonText: {
    fontSize: fontSize.base,
    fontWeight: fontWeight.semibold,
    color: colors.white,
  },
  
  // Icon styles
  iconContainer: {
    width: 64,
    height: 64,
    backgroundColor: colors.blue900,
    borderRadius: borderRadius.full,
    borderWidth: 1,
    borderColor: colors.blue700,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.md,
  },
  
  iconSmall: {
    marginRight: spacing.sm,
  },
  
  // Loading styles
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: colors.gray900,
  },
  
  loadingSpinner: {
    marginBottom: spacing.lg,
  },
  
  loadingTitle: {
    fontSize: fontSize.xxl,
    fontWeight: fontWeight.bold,
    color: colors.white,
    marginBottom: spacing.sm,
  },
  
  loadingDescription: {
    fontSize: fontSize.base,
    color: colors.gray400,
    marginBottom: spacing.md,
    textAlign: 'center',
  },
  
  // Progress indicator styles
  progressContainer: {
    width: width * 0.8,
    maxWidth: 400,
  },
  
  progressItem: {
    backgroundColor: colors.gray800,
    borderWidth: 1,
    borderColor: colors.gray700,
    borderRadius: borderRadius.lg,
    padding: spacing.md,
    marginBottom: spacing.sm,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  
  progressItemCompleted: {
    borderColor: colors.green700,
  },
  
  progressText: {
    fontSize: fontSize.sm,
    color: colors.gray300,
  },
  
  // Score styles
  scoreContainer: {
    alignItems: 'center',
    padding: spacing.md,
  },
  
  scoreValue: {
    fontSize: fontSize.xxxxl,
    fontWeight: fontWeight.bold,
    marginBottom: spacing.xs,
  },
  
  scoreLabel: {
    fontSize: fontSize.xs,
    color: colors.gray400,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  
  scoreHigh: {
    color: colors.green400,
  },
  
  scoreMedium: {
    color: colors.yellow400,
  },
  
  scoreLow: {
    color: colors.red400,
  },
  
  // Grid styles
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginHorizontal: -spacing.sm,
  },
  
  gridItem: {
    flex: 1,
    marginHorizontal: spacing.sm,
    minWidth: width / 2 - spacing.lg,
  },
  
  gridItemFull: {
    width: '100%',
    marginHorizontal: spacing.sm,
  },
  
  // Badge styles
  badge: {
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: borderRadius.full,
    borderWidth: 1,
  },
  
  badgeHigh: {
    backgroundColor: colors.green900,
    borderColor: colors.green700,
  },
  
  badgeMedium: {
    backgroundColor: colors.yellow900,
    borderColor: colors.yellow700,
  },
  
  badgeLow: {
    backgroundColor: colors.red900,
    borderColor: colors.red700,
  },
  
  badgeText: {
    fontSize: fontSize.xs,
    fontWeight: fontWeight.medium,
  },
  
  badgeTextHigh: {
    color: colors.green300,
  },
  
  badgeTextMedium: {
    color: colors.yellow300,
  },
  
  badgeTextLow: {
    color: colors.red300,
  },
  
  // Feature highlight styles
  featureContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-around',
    paddingTop: spacing.lg,
    borderTopWidth: 1,
    borderTopColor: colors.gray700,
    marginTop: spacing.lg,
  },
  
  featureItem: {
    alignItems: 'center',
  },
  
  featureText: {
    fontSize: fontSize.sm,
    color: colors.gray400,
    marginLeft: spacing.xs,
  },
  
  // Alert styles
  alert: {
    backgroundColor: colors.yellow900,
    borderWidth: 1,
    borderColor: colors.yellow700,
    borderRadius: borderRadius.lg,
    padding: spacing.md,
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginTop: spacing.md,
  },
  
  alertIcon: {
    marginRight: spacing.sm,
    marginTop: 2,
  },
  
  alertContent: {
    flex: 1,
  },
  
  alertTitle: {
    fontSize: fontSize.base,
    fontWeight: fontWeight.medium,
    color: colors.yellow300,
    marginBottom: spacing.xs,
  },
  
  alertDescription: {
    fontSize: fontSize.sm,
    color: colors.yellow200,
    lineHeight: 20,
  },
});

export default styles;
