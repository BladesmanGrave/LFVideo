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

export interface TableRow {
	feature: string;
	cursor: string;
	windsurf: string;
	win: 'cursor' | 'windsurf' | 'neutral';
}

interface Props {
	eyebrow?: string;
	title: string;
	headers: string[]; // e.g. ["对比项", "Cursor Rules (.mdc)", "Windsurf (Workflows)"]
	rows: TableRow[];
	background?: BackgroundVariant;
	startFrame?: number;
	rowStagger?: number;
	highlightCell?: string; // row-col indexing (e.g. "2-3" or "3-3") to blink-highlight
}

const TableCell: React.FC<{
	content: string;
	isHeader?: boolean;
	isWinner?: boolean;
	winColor?: string;
	align?: 'left' | 'center';
	colIndex: number;
	rowIndex: number;
	highlightActive: boolean;
	dense?: boolean;
}> = ({content, isHeader = false, isWinner = false, winColor = COLORS.accent[1], align = 'left', colIndex, rowIndex, highlightActive, dense = false}) => {
	const blinkAnimName = `cell-blink-${rowIndex}-${colIndex}`;

	return (
		<div
			style={{
				flex: colIndex === 0 ? 1.2 : 1.5,
				padding: `${dense ? SPACING.sm : SPACING.md}px ${SPACING.lg}px`,
				fontSize: isHeader ? FONT_SIZE.body + (dense ? 0 : 2) : FONT_SIZE.body - (dense ? 2 : 1),
				fontWeight: isHeader ? 900 : colIndex === 0 ? 800 : 500,
				color: isHeader 
					? COLORS.text.primary 
					: colIndex === 0 
						? COLORS.text.primary 
						: COLORS.text.secondary,
				display: 'flex',
				alignItems: 'center',
				justifyContent: align === 'center' ? 'center' : 'flex-start',
				background: isHeader 
					? 'rgba(40, 26, 44, 0.7)' 
					: isWinner && highlightActive
						? `${winColor}10` 
						: 'transparent',
				border: isWinner && highlightActive
					? `2px solid ${winColor}`
					: '1.5px solid rgba(255, 255, 255, 0.05)',
				borderRadius: isWinner && highlightActive ? RADIUS.md : 0,
				position: 'relative',
				overflow: 'hidden',
				transition: 'all 0.5s ease',
				boxShadow: isWinner && highlightActive ? `0 0 15px ${winColor}25` : 'none',
				animation: isWinner && highlightActive ? `${blinkAnimName} 2s infinite ease-in-out` : 'none',
			}}
		>
			{isWinner && highlightActive && (
				<style>{`
					@keyframes ${blinkAnimName} {
						0% { border-color: ${winColor}55; box-shadow: 0 0 5px ${winColor}15; }
						50% { border-color: ${winColor}ff; box-shadow: 0 0 20px ${winColor}44; }
						100% { border-color: ${winColor}55; box-shadow: 0 0 5px ${winColor}15; }
					}
				`}</style>
			)}
			<span style={{zIndex: 1}}>{content}</span>
		</div>
	);
};

export const TableScene: React.FC<Props> = ({
	eyebrow,
	title,
	headers,
	rows,
	background = 'gradient',
	startFrame = 25,
	rowStagger = 15,
	highlightCell,
}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();

	// Compact layout once the table has many rows, so tall tables stay inside
	// the frame and clear of the bottom caption safe-area.
	const dense = rows.length > 4;

	// Header row pop-up animation
	const headerProgress = spring({
		fps,
		frame: frame - startFrame,
		config: SPRING.snappy,
	});

	const headerOpacity = interpolate(headerProgress, [0, 1], [0, 1]);
	const headerScaleY = interpolate(headerProgress, [0, 1], [0.8, 1]);

	// Highlight threshold frame (110f / ~3.6 seconds is active)
	const highlightActive = frame > 110;

	return (
		<AnimatedBackground variant={background}>
			<AbsoluteFill
				style={{
					fontFamily: FONT_FAMILY,
					// Reserve a bottom safe-area (~180px) for the caption overlay so
					// tall tables never crowd or sit under the burned-in subtitles.
					padding: `${SPACING.xl}px ${SPACING.gutter}px 180px`,
					display: 'flex',
					flexDirection: 'column',
					justifyContent: 'center',
				}}
			>
				<TitleFrame eyebrow={eyebrow} title={title} />

				{/* Table Wrapper Grid */}
				<div
					style={{
						display: 'flex',
						flexDirection: 'column',
						background: 'rgba(40, 26, 44, 0.3)',
						borderRadius: RADIUS.lg,
						border: '1.5px solid rgba(255, 255, 255, 0.08)',
						backdropFilter: 'blur(16px)',
						boxShadow: '0 20px 50px -10px rgba(0, 0, 0, 0.7)',
						overflow: 'hidden',
						marginTop: dense ? SPACING.lg : SPACING.xl,
					}}
				>
					{/* Table Header */}
					<div
						style={{
							display: 'flex',
							background: 'rgba(40, 26, 44, 0.8)',
							borderBottom: '2px solid rgba(255, 255, 255, 0.15)',
							opacity: headerOpacity,
							transform: `scaleY(${headerScaleY})`,
							transformOrigin: 'top',
						}}
					>
						{headers.map((header, colIndex) => (
							<TableCell
								key={header}
								content={header}
								isHeader
								colIndex={colIndex}
								rowIndex={0}
								align={colIndex === 0 ? 'left' : 'center'}
								highlightActive={false}
								dense={dense}
							/>
						))}
					</div>

					{/* Table Rows */}
					{rows.map((row, rowIndex) => {
						const rowStart = startFrame + (rowIndex + 1) * rowStagger;
						
						// Staggered spring for row fade/slide
						const rowProgress = spring({
							fps,
							frame: frame - rowStart,
							config: SPRING.snappy,
						});

						const rowOpacity = interpolate(rowProgress, [0, 1], [0, 1]);
						const rowTranslateY = interpolate(rowProgress, [0, 1], [30, 0]);

						return (
							<div
								key={row.feature}
								style={{
									display: 'flex',
									opacity: rowOpacity,
									transform: `translateY(${rowTranslateY}px)`,
									borderBottom: rowIndex === rows.length - 1 ? 'none' : '1.5px solid rgba(255, 255, 255, 0.05)',
									background: rowIndex % 2 === 1 ? 'rgba(255, 255, 255, 0.015)' : 'transparent',
								}}
							>
								{/* Feature label cell */}
								<TableCell
									content={row.feature}
									colIndex={0}
									rowIndex={rowIndex + 1}
									align="left"
									highlightActive={false}
									dense={dense}
								/>

								{/* Cursor Cell */}
								<TableCell
									content={row.cursor}
									colIndex={1}
									rowIndex={rowIndex + 1}
									isWinner={row.win === 'cursor'}
									winColor={COLORS.accent[0]}
									align="center"
									highlightActive={highlightActive}
									dense={dense}
								/>

								{/* Windsurf Cell */}
								<TableCell
									content={row.windsurf}
									colIndex={2}
									rowIndex={rowIndex + 1}
									isWinner={row.win === 'windsurf'}
									winColor={COLORS.accent[1]}
									align="center"
									highlightActive={highlightActive}
									dense={dense}
								/>
							</div>
						);
					})}
				</div>
			</AbsoluteFill>
		</AnimatedBackground>
	);
};
