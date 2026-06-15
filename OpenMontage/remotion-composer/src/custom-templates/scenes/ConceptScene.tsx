import React from 'react';
import {
	AbsoluteFill,
	interpolate,
	spring,
	useCurrentFrame,
	useVideoConfig,
} from 'remotion';
import {AnimatedBackground, TitleFrame} from '../primitives';
import type {BackgroundVariant} from '../primitives';
import {COLORS, FONT_SIZE, SPACING, RADIUS, SPRING} from '../theme/tokens';
import {FONT_FAMILY} from '../theme/fonts';

export interface ConceptItem {
	label: string;
	title: string;
	desc: string;
	icon: string;
}

interface Props {
	eyebrow?: string;
	title: string;
	items: ConceptItem[];
	background?: BackgroundVariant;
	// 卡片入场起始帧 + 间隔
	cardStart?: number;
	cardStagger?: number;
}

const ItemCard: React.FC<{
	item: ConceptItem;
	color: string;
	startFrame: number;
	index: number;
}> = ({item, color, startFrame, index}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const progress = spring({
		fps,
		frame: frame - startFrame,
		config: SPRING.snappy,
	});
	const opacity = interpolate(progress, [0, 1], [0, 1]);
	const translateY = interpolate(progress, [0, 1], [60, 0]);
	const scale = interpolate(progress, [0, 1], [0.95, 1]);

	// Unique animation names per card index
	const cardAnimName = `card-glow-${index}`;
	const iconAnimName = `icon-float-${index}`;

	return (
		<div
			className={`concept-card-${index}`}
			style={{
				opacity,
				transform: `translateY(${translateY}px) scale(${scale})`,
				display: 'flex',
				alignItems: 'flex-start',
				gap: SPACING.md,
				background: 'rgba(40, 26, 44, 0.45)', // warm deep glass
				border: `1.5px solid ${color}22`,
				borderRadius: RADIUS.lg,
				padding: `${SPACING.md + 4}px ${SPACING.lg}px`,
				marginBottom: SPACING.md,
				backdropFilter: 'blur(16px)',
				boxShadow: '0 10px 40px -10px rgba(0, 0, 0, 0.5), inset 0 1px 1px rgba(255, 255, 255, 0.05)',
				animation: `${cardAnimName} 6s infinite ease-in-out`,
				animationDelay: `${index * 0.5}s`,
				position: 'relative',
				overflow: 'hidden',
			}}
		>
			{/* Inject card-specific CSS animations dynamically */}
			<style>{`
				@keyframes ${cardAnimName} {
					0% { border-color: ${color}22; box-shadow: 0 10px 40px -10px rgba(0, 0, 0, 0.5), 0 0 0px ${color}00; }
					50% { border-color: ${color}77; box-shadow: 0 10px 40px -10px rgba(0, 0, 0, 0.7), 0 0 18px ${color}22; }
					100% { border-color: ${color}22; box-shadow: 0 10px 40px -10px rgba(0, 0, 0, 0.5), 0 0 0px ${color}00; }
				}
				@keyframes ${iconAnimName} {
					0% { transform: translateY(0px) rotate(0deg); }
					50% { transform: translateY(-6px) rotate(4deg); }
					100% { transform: translateY(0px) rotate(0deg); }
				}
			`}</style>

			{/* Soft color glow spot behind icon */}
			<div
				style={{
					position: 'absolute',
					left: -50,
					top: -50,
					width: 150,
					height: 150,
					borderRadius: '50%',
					background: `radial-gradient(circle, ${color}15 0%, transparent 70%)`,
					pointerEvents: 'none',
				}}
			/>

			{/* Animated Icon Box */}
			<div
				style={{
					width: 80,
					height: 80,
					borderRadius: RADIUS.md,
					background: `${color}18`,
					border: `1.5px solid ${color}44`,
					display: 'flex',
					alignItems: 'center',
					justifyContent: 'center',
					fontSize: 40,
					flexShrink: 0,
					boxShadow: `0 4px 20px -2px ${color}18`,
					animation: `${iconAnimName} 5s infinite ease-in-out`,
					animationDelay: `${index * 0.3}s`,
				}}
			>
				{item.icon}
			</div>

			<div style={{flex: 1, zIndex: 1}}>
				<div
					style={{
						fontSize: FONT_SIZE.caption,
						letterSpacing: 4,
						color,
						fontWeight: 800,
						marginBottom: SPACING.xs - 2,
						textTransform: 'uppercase',
						opacity: 0.9,
					}}
				>
					{item.label}
				</div>
				<div
					style={{
						fontSize: FONT_SIZE.subtitle,
						fontWeight: 800,
						color: COLORS.text.primary,
						marginBottom: SPACING.xs,
						lineHeight: 1.2,
						letterSpacing: -0.5,
					}}
				>
					{item.title}
				</div>
				<div
					style={{
						fontSize: FONT_SIZE.body,
						color: COLORS.text.secondary,
						lineHeight: 1.65,
					}}
				>
					{item.desc}
				</div>
			</div>
		</div>
	);
};

export const ConceptScene: React.FC<Props> = ({
	eyebrow,
	title,
	items,
	background = 'gradient',
	cardStart = 20,
	cardStagger = 25,
}) => {
	return (
		<AnimatedBackground variant={background}>
			<AbsoluteFill
				style={{
					fontFamily: FONT_FAMILY,
					padding: `${SPACING.xl}px ${SPACING.gutter}px`,
					display: 'flex',
					flexDirection: 'column',
					justifyContent: 'center',
				}}
			>
				<TitleFrame eyebrow={eyebrow} title={title} />
				{items.map((item, i) => (
					<ItemCard
						key={item.title}
						item={item}
						color={COLORS.accent[i % COLORS.accent.length]}
						startFrame={cardStart + i * cardStagger}
						index={i}
					/>
				))}
			</AbsoluteFill>
		</AnimatedBackground>
	);
};
