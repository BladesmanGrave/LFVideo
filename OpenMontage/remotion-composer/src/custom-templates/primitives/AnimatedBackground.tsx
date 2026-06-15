import React from 'react';
import {AbsoluteFill, useCurrentFrame, interpolate} from 'remotion';
import {COLORS} from '../theme/tokens';

export type BackgroundVariant = 'gradient' | 'grid' | 'particles';

interface Props {
	variant?: BackgroundVariant;
	children?: React.ReactNode;
}

// 1. Vercel-style Fluid Mesh Gradient (Translucent to show the sci-fi video)
const MeshGradientBg: React.FC = () => {
	const frame = useCurrentFrame();
	
	// Slowly drift and rotate coordinates dynamically using sine/cosine
	const x1 = Math.sin(frame * 0.004) * 150 + 200;
	const y1 = Math.cos(frame * 0.005) * 150 + 300;
	const x2 = Math.cos(frame * 0.003) * 150 + 1500;
	const y2 = Math.sin(frame * 0.004) * 150 + 800;
	const x3 = Math.sin(frame * 0.003) * 200 + 960;
	const y3 = Math.cos(frame * 0.006) * 150 + 540;

	return (
		<AbsoluteFill style={{backgroundColor: 'rgba(26, 16, 28, 0.6)', overflow: 'hidden'}}>
			{/* Inject Keyframe Styles */}
			<style>{`
				@keyframes drift-slow {
					0% { transform: scale(1) translate(0px, 0px) rotate(0deg); }
					50% { transform: scale(1.1) translate(40px, -60px) rotate(180deg); }
					100% { transform: scale(1) translate(0px, 0px) rotate(360deg); }
				}
			`}</style>

			{/* Color Blobs */}
			<div
				style={{
					position: 'absolute',
					left: x1 - 400,
					top: y1 - 400,
					width: 800,
					height: 800,
					borderRadius: '50%',
					background: `radial-gradient(circle, ${COLORS.accent[0]}22 0%, transparent 70%)`,
					filter: 'blur(100px)',
					animation: 'drift-slow 25s infinite ease-in-out',
				}}
			/>
			<div
				style={{
					position: 'absolute',
					left: x2 - 400,
					top: y2 - 400,
					width: 800,
					height: 800,
					borderRadius: '50%',
					background: `radial-gradient(circle, ${COLORS.accent[1]}18 0%, transparent 70%)`,
					filter: 'blur(120px)',
					animation: 'drift-slow 30s infinite ease-in-out reverse',
				}}
			/>
			<div
				style={{
					position: 'absolute',
					left: x3 - 500,
					top: y3 - 500,
					width: 1000,
					height: 1000,
					borderRadius: '50%',
					background: `radial-gradient(circle, ${COLORS.accent[2]}12 0%, transparent 75%)`,
					filter: 'blur(140px)',
					animation: 'drift-slow 35s infinite ease-in-out',
				}}
			/>
		</AbsoluteFill>
	);
};

// 2. High-Tech Grid with Laser Sweeps and Underlaid Mesh Gradient
const GridBg: React.FC = () => {
	const frame = useCurrentFrame();
	const gridOffset = (frame * 0.4) % 60;
	
	// Dynamic vertical laser sweep position
	const sweepX = interpolate(frame % 300, [0, 300], [-300, 2220]);

	return (
		<AbsoluteFill>
			{/* Underlaid Mesh Gradient for ultra high quality */}
			<MeshGradientBg />

			{/* Transparent Tech Grid Overlay */}
			<AbsoluteFill
				style={{
					backgroundImage: `linear-gradient(${COLORS.line} 1px, transparent 1px), linear-gradient(90deg, ${COLORS.line} 1px, transparent 1px)`,
					backgroundSize: '60px 60px',
					backgroundPosition: `${gridOffset}px ${gridOffset}px`,
					opacity: 0.8,
				}}
			/>

			{/* Glow Dot at intersections or moving light sweep */}
			<div
				style={{
					position: 'absolute',
					left: sweepX,
					top: 0,
					width: '150px',
					height: '100%',
					background: `linear-gradient(90deg, transparent, rgba(255, 179, 71, 0.08), transparent)`,
					pointerEvents: 'none',
				}}
			/>
		</AbsoluteFill>
	);
};

// 3. Constellation Particles with soft glow and organic drift
const PARTICLES = Array.from({length: 32}, (_, i) => ({
	x: (i * 137.5) % 100,
	y: (i * 73.3) % 100,
	size: 4 + (i % 3) * 2,
	speed: 0.2 + (i % 4) * 0.1,
	color: COLORS.accent[i % COLORS.accent.length],
	driftRadius: 5 + (i % 5) * 2,
	driftSpeed: 0.01 + (i % 3) * 0.005,
}));

const ParticlesBg: React.FC = () => {
	const frame = useCurrentFrame();
	return (
		<AbsoluteFill style={{backgroundColor: 'rgba(22, 13, 24, 0.7)', overflow: 'hidden'}}>
			{/* Drift particles based on trigonometric waves */}
			{PARTICLES.map((p, i) => {
				const time = frame * p.driftSpeed;
				const curX = p.x + Math.sin(time) * p.driftRadius * 0.15;
				const curY = ((p.y - frame * p.speed * 0.03 + 100) % 100);

				return (
					<React.Fragment key={i}>
						{/* Particle Glow Sphere */}
						<div
							style={{
								position: 'absolute',
								left: `${curX}%`,
								top: `${curY}%`,
								width: p.size,
								height: p.size,
								borderRadius: '50%',
								backgroundColor: p.color,
								opacity: 0.5,
								boxShadow: `0 0 ${p.size * 3}px ${p.color}, 0 0 ${p.size * 6}px ${p.color}aa`,
								transform: 'translate(-50%, -50%)',
							}}
						/>
					</React.Fragment>
				);
			})}
		</AbsoluteFill>
	);
};

export const AnimatedBackground: React.FC<Props> = ({
	variant = 'gradient',
	children,
}) => {
	return (
		<AbsoluteFill>
			{variant === 'gradient' && <MeshGradientBg />}
			{variant === 'grid' && <GridBg />}
			{variant === 'particles' && <ParticlesBg />}
			<AbsoluteFill style={{zIndex: 10}}>{children}</AbsoluteFill>
		</AbsoluteFill>
	);
};
