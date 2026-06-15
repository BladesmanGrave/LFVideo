import React from 'react';
import {
	AbsoluteFill,
	interpolate,
	spring,
	useCurrentFrame,
	useVideoConfig,
} from 'remotion';
import {AnimatedBackground} from '../primitives';
import type {BackgroundVariant} from '../primitives';
import {COLORS, FONT_SIZE, SPACING} from '../theme/tokens';
import {FONT_FAMILY} from '../theme/fonts';

interface Props {
	title: string;
	subtitle?: string;
	background?: BackgroundVariant;
}

export const IntroScene: React.FC<Props> = ({
	title,
	subtitle,
	background = 'particles',
}) => {
	const frame = useCurrentFrame();
	const {fps, durationInFrames} = useVideoConfig();

	const enter = spring({fps, frame, config: {damping: 20, stiffness: 90}});
	const opacity = interpolate(enter, [0, 1], [0, 1]);
	const scale = interpolate(enter, [0, 1], [0.9, 1]);

	// 片尾淡出
	const fadeOut = interpolate(
		frame,
		[durationInFrames - 15, durationInFrames],
		[1, 0],
		{extrapolateLeft: 'clamp'}
	);

	return (
		<AnimatedBackground variant={background}>
			{/* Inject Text Shine Animations */}
			<style>{`
				@keyframes text-shine {
					0% { background-position: 0% 50%; }
					100% { background-position: 200% 50%; }
				}
				@keyframes subtitle-reveal {
					0% { opacity: 0; transform: translateY(20px); }
					100% { opacity: 0.85; transform: translateY(0); }
				}
			`}</style>

			<AbsoluteFill
				style={{
					fontFamily: FONT_FAMILY,
					justifyContent: 'center',
					alignItems: 'center',
					textAlign: 'center',
					opacity: opacity * fadeOut,
					transform: `scale(${scale})`,
				}}
			>
				{/* Glowing Ambient Behind Title */}
				<div
					style={{
						position: 'absolute',
						width: 600,
						height: 250,
						borderRadius: '50%',
						background: 'radial-gradient(circle, rgba(255, 179, 71, 0.12) 0%, transparent 70%)',
						filter: 'blur(80px)',
						zIndex: 0,
						pointerEvents: 'none',
					}}
				/>

				<div
					style={{
						fontSize: FONT_SIZE.display,
						fontWeight: 900,
						lineHeight: 1.15,
						marginBottom: SPACING.lg,
						maxWidth: 1500,
						padding: '0 80px',
						letterSpacing: -1.5,
						background: `linear-gradient(90deg, ${COLORS.text.primary} 0%, ${COLORS.accent[0]} 25%, ${COLORS.accent[1]} 50%, ${COLORS.accent[3]} 75%, ${COLORS.text.primary} 100%)`,
						backgroundSize: '200% auto',
						WebkitBackgroundClip: 'text',
						WebkitTextFillColor: 'transparent',
						animation: 'text-shine 8s linear infinite',
						zIndex: 1,
					}}
				>
					{title}
				</div>
				{subtitle && (
					<div
						style={{
							fontSize: FONT_SIZE.subtitle,
							color: COLORS.text.secondary,
							fontWeight: 600,
							letterSpacing: 2,
							textTransform: 'uppercase',
							animation: 'subtitle-reveal 1.2s cubic-bezier(0.16, 1, 0.3, 1) forwards',
							animationDelay: '0.4s',
							opacity: 0, // Controlled by CSS animation
							zIndex: 1,
						}}
					>
						{subtitle}
					</div>
				)}
			</AbsoluteFill>
		</AnimatedBackground>
	);
};
